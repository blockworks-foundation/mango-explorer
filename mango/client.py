# # ⚠ Warning
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
# NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# [🥭 Mango Markets](https://mango.markets/) support is available at:
#   [Docs](https://docs.mango.markets/)
#   [Discord](https://discord.gg/67jySBhxrg)
#   [Twitter](https://twitter.com/mangomarkets)
#   [Github](https://github.com/blockworks-foundation)
#   [Email](mailto:hello@blockworks.foundation)

import datetime
import json
import logging
import requests
import time
import typing


from base64 import b64decode, b64encode
from collections.abc import Mapping
from decimal import Decimal
from solana.blockhash import Blockhash, BlockhashCache
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.rpc.commitment import Commitment, Processed, Finalized
from solana.rpc.providers.http import HTTPProvider
from solana.rpc.types import DataSliceOpts, MemcmpOpts, RPCMethod, RPCResponse, TokenAccountOpts, TxOpts
from solana.transaction import Transaction

from .constants import SOL_DECIMAL_DIVISOR
from .instructionreporter import InstructionReporter
from .logmessages import expand_log_messages
from .text import indent_collection_as_str


_STUB_TRANSACTION_SIGNATURE: str = "stub-for-already-submitted-transaction-signature"


# # 🥭 CompoundException class
#
# A `CompoundException` exception can hold all exceptions that were raised when trying to read or
# write to Solana.
#
# The `Client` can rotate through multiple providers, switching when certain `Exception`s are thrown.
# This exception allows all those exceptions to be gathered and inspected should all providers fail.
#
class CompoundException(Exception):
    def __init__(self, name: str, all_exceptions: typing.Sequence[Exception]) -> None:
        super().__init__(f"[{name}] Multiple errors captured for event")
        self.name: str = name
        self.all_exceptions: typing.Sequence[Exception] = all_exceptions

    def __str__(self) -> str:
        details: str = indent_collection_as_str(self.all_exceptions)
        return f"""« CompoundException with {len(self.all_exceptions)} inner exceptions:
    {details}
»"""


# # 🥭 ClientException class
#
# A `ClientException` exception base class that allows trapping and handling rate limiting
# independent of other error handling.
#
class ClientException(Exception):
    def __init__(self, message: str, name: str, cluster_url: str) -> None:
        super().__init__(message)
        self.message: str = message
        self.name: str = name
        self.cluster_url: str = cluster_url

    def __str__(self) -> str:
        return f"« {type(self)} '{self.message}' from '{self.name}' on {self.cluster_url} »"

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 RateLimitException class
#
# A `RateLimitException` exception base class that allows trapping and handling rate limiting
# independent of other error handling.
#
class RateLimitException(ClientException):
    pass


# # 🥭 TooMuchBandwidthRateLimitException class
#
# A `TooMuchBandwidthRateLimitException` exception that specialises the `RateLimitException`
# for when too much bandwidth has been consumed.
#
class TooMuchBandwidthRateLimitException(RateLimitException):
    pass


# # 🥭 TooManyRequestsRateLimitException class
#
# A `TooManyRequestsRateLimitException` exception that specialises the `RateLimitException`
# for when too many requests have been sent in a short time.
#
class TooManyRequestsRateLimitException(RateLimitException):
    pass


# # 🥭 BlockhashNotFoundException class
#
# A `BlockhashNotFoundException` exception allows trapping and handling exceptions when a blockhash is sent that
# the node doesn't understand. This can happen when the blockhash is too old (and the node no longer
# considers it 'recent') or when it's too new (and hasn't yet made it to the node that is responding).
#
class BlockhashNotFoundException(ClientException):
    def __init__(self, name: str, cluster_url: str, blockhash: typing.Optional[Blockhash] = None) -> None:
        message: str = f"Blockhash '{blockhash}' not found on {cluster_url}."
        super().__init__(message, name, cluster_url)
        self.blockhash: typing.Optional[Blockhash] = blockhash

    def __str__(self) -> str:
        return f"« BlockhashNotFoundException '{self.name}' [{self.blockhash}] on {self.cluster_url} »"


# # 🥭 NodeIsBehindException class
#
# A `NodeIsBehindException` exception allows trapping and handling exceptions when a node is behind by too
# many slots.
#
class NodeIsBehindException(ClientException):
    def __init__(self, name: str, cluster_url: str, slots_behind: int) -> None:
        message: str = f"Node is behind by {slots_behind} slots."
        super().__init__(message, name, cluster_url)
        self.slots_behind: int = slots_behind

    def __str__(self) -> str:
        return f"« NodeIsBehindException '{self.name}' [behind by {self.slots_behind} slots] on {self.cluster_url} »"


# # 🥭 TransactionAlreadyProcessedException class
#
# A `TransactionAlreadyProcessedException` exception indicates that a transaction with that signature and
# recent blockhash has already been processed.
#
# This can be a normal consequence of the stale slot checking/resubmission (which will mean it is ignored)
# or it can indicate an actual problem.
#
class TransactionAlreadyProcessedException(RateLimitException):
    pass


# # 🥭 StaleSlotException class
#
# A `StaleSlotException` exception allows trapping and handling exceptions when data is received from
#
class StaleSlotException(ClientException):
    def __init__(self, name: str, cluster_url: str, latest_seen_slot: int, just_returned_slot: int) -> None:
        message: str = f"Stale slot received - received data from slot {just_returned_slot} having previously seen slot {latest_seen_slot}."
        super().__init__(message, name, cluster_url)
        self.latest_seen_slot: int = latest_seen_slot
        self.just_returned_slot: int = just_returned_slot

    def __str__(self) -> str:
        return f"« StaleSlotException '{self.name}' [received data from slot {self.just_returned_slot} having previously seen slot {self.latest_seen_slot}] on {self.cluster_url} »"


# # 🥭 FailedToFetchBlockhashException class
#
# A `FailedToFetchBlockhashException` exception allows trapping and handling exceptions when we fail
# to fetch a recent or distinct blockhash.
#
class FailedToFetchBlockhashException(ClientException):
    def __init__(self, message: str, name: str, cluster_url: str, pauses: typing.Sequence[float]) -> None:
        super().__init__(message, name, cluster_url)
        self.pauses: typing.Sequence[float] = pauses

    def __str__(self) -> str:
        if len(self.pauses) == 0:
            return f"« FailedToFetchBlockhashException '{self.name}' Failed to get recent blockhash on {self.cluster_url} »"

        pauses_text = ",".join(f"{pause}" for pause in self.pauses[:-1])
        return f"« FailedToFetchBlockhashException '{self.name}' Failed to get a fresh, recent blockhash after {len(self.pauses)} attempts - paused {pauses_text} seconds between attempts on {self.cluster_url} »"


# # 🥭 TransactionException class
#
# A `TransactionException` exception that can provide additional error data, or at least better output
# of problems at the right place.
#
class TransactionException(ClientException):
    def __init__(self, transaction: typing.Optional[Transaction], message: str, code: int, name: str, cluster_url: str, rpc_method: str, request_text: str, response_text: str, accounts: typing.Union[str, typing.List[str], None], errors: typing.Union[str, typing.List[str], None], logs: typing.Union[str, typing.List[str], None], instruction_reporter: InstructionReporter = InstructionReporter()) -> None:
        super().__init__(message, name, cluster_url)
        self.transaction: typing.Optional[Transaction] = transaction
        self.code: int = code
        self.rpc_method: str = rpc_method
        self.request_text: str = request_text
        self.response_text: str = response_text

        def _ensure_list(item: typing.Union[str, typing.List[str], None]) -> typing.List[str]:
            if item is None:
                return []
            if isinstance(item, str):
                return [item]
            if isinstance(item, list):
                return item
            return [f"{item}"]
        self.accounts: typing.Sequence[str] = _ensure_list(accounts)
        self.errors: typing.Sequence[str] = _ensure_list(errors)
        self.logs: typing.Sequence[str] = expand_log_messages(_ensure_list(logs))
        self.instruction_reporter: InstructionReporter = instruction_reporter

    def __str__(self) -> str:
        try:
            request_details: str = ""
            response_details: str = ""
            if logging.DEBUG >= logging.root.level:
                request_details = f"""
    Request:
        {self.request_text}"""
            response_details = f"""
    Response:
        {self.response_text}"""
            transaction_details = ""
            if self.transaction is not None:
                instruction_details = "\n".join(
                    list(map(self.instruction_reporter.report, self.transaction.instructions)))
                transaction_details = "\n    Instructions:\n        " + instruction_details.replace("\n", "\n        ")
            accounts = "No Accounts"
            if len(self.accounts) > 0:
                accounts = "\n        ".join([f"{item}".replace("\n", "\n        ") for item in self.accounts])
            errors = "No Errors"
            if len(self.errors) > 0:
                errors = "\n        ".join([f"{item}".replace("\n", "\n        ") for item in self.errors])
            logs = "No Logs"
            if len(self.logs) > 0:
                logs = "\n        ".join([f"{item}".replace("\n", "\n        ") for item in self.logs])
            return f"""« TransactionException in '{self.name}' [{self.rpc_method}]: {self.code}:: {self.message}{transaction_details}
    Accounts:
        {accounts}
    Errors:
        {errors}
    Logs:
        {logs}{request_details}{response_details}
»"""
        except Exception as exception:
            return f"TransactionException printing failed with: {exception}"

    def __repr__(self) -> str:
        return f"{self}"


UnspecifiedCommitment = Commitment("unspecified")
UnspecifiedEncoding = "unspecified"


# # 🥭 SlotHolder class
#
# A `SlotHolder` shares the latest slot across multiple `RPCCaller`s.
#
class SlotHolder:
    def __init__(self) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.__latest_slot: int = 0

    @property
    def latest_slot(self) -> int:
        return self.__latest_slot

    def require_data_from_fresh_slot(self, latest_slot: typing.Optional[int] = None) -> None:
        latest: int = latest_slot or self.latest_slot
        if latest >= self.latest_slot:
            self.__latest_slot = latest + 1
            self._logger.debug(f"Requiring data from slot {self.latest_slot} onwards now.")

    def is_acceptable(self, slot_to_check: int) -> bool:
        if slot_to_check < self.__latest_slot:
            return False

        if slot_to_check > self.__latest_slot:
            self.__latest_slot = slot_to_check
            self._logger.debug(f"Only accepting data from slot {self.latest_slot} onwards now.")
        return True


# # 🥭 RPCCaller class
#
# A `RPCCaller` extends the HTTPProvider with better error handling.
#
class RPCCaller(HTTPProvider):
    def __init__(self, name: str, cluster_url: str, stale_data_pauses_before_retry: typing.Sequence[float], slot_holder: SlotHolder, instruction_reporter: InstructionReporter):
        super().__init__(cluster_url)
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.name: str = name
        self.cluster_url: str = cluster_url
        self.stale_data_pauses_before_retry: typing.Sequence[float] = stale_data_pauses_before_retry
        self.slot_holder: SlotHolder = slot_holder
        self.instruction_reporter: InstructionReporter = instruction_reporter

    def require_data_from_fresh_slot(self, latest_slot: typing.Optional[int] = None) -> None:
        self.slot_holder.require_data_from_fresh_slot(latest_slot)

    def make_request(self, method: RPCMethod, *params: typing.Any) -> RPCResponse:
        # No pauses specified means this funcitonality is turned off.
        if len(self.stale_data_pauses_before_retry) == 0:
            return self.__make_request(method, *params)

        at_least_one_submission: bool = False
        last_stale_slot_exception: StaleSlotException
        for pause in [*self.stale_data_pauses_before_retry, 0]:
            try:
                return self.__make_request(method, *params)
            except TransactionAlreadyProcessedException as transaction_already_processed_exception:
                if not at_least_one_submission:
                    raise transaction_already_processed_exception

                # The transaction has already been processed (even though we previously got a stale slot
                # response). So, yay? It's good that it was successfully handled (and presumably processed)
                # and it means we can safely ignore this exception, but it does leave us with no proper
                # response to return.
                #
                # Return fake data in the expected structure for now, and try to figure out a better way.
                return {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "result": _STUB_TRANSACTION_SIGNATURE,
                }
            except StaleSlotException as exception:
                last_stale_slot_exception = exception
                self._logger.debug(f"Will retry after pause of {pause} seconds after getting stale slot: {exception}")
                time.sleep(pause)
            at_least_one_submission = True

        # They've all failed.
        raise last_stale_slot_exception

    def __make_request(self, method: RPCMethod, *params: typing.Any) -> RPCResponse:
        # This is the entire method in HTTPProvider that we're overriding here:
        #
        # """Make an HTTP request to an http rpc endpoint."""
        # request_kwargs = self._before_request(method=method, params=params, is_async=False)
        # raw_response = requests.post(**request_kwargs)
        # return self._after_request(raw_response=raw_response, method=method)

        request_kwargs = self._before_request(method=method, params=params, is_async=False)
        raw_response = requests.post(**request_kwargs)

        # Some custom exceptions specifically for rate-limiting. This allows calling code to handle this
        # specific case if they so choose.
        #
        # "You will see HTTP respose codes 429 for too many requests or 413 for too much bandwidth."
        if raw_response.status_code == 413:
            raise TooMuchBandwidthRateLimitException(
                f"Rate limited (too much bandwidth) calling method '{method}'.", self.name, self.cluster_url)
        elif raw_response.status_code == 429:
            raise TooManyRequestsRateLimitException(
                f"Rate limited (too many requests) calling method '{method}'.", self.name, self.cluster_url)

        # Not a rate-limit problem, but maybe there was some other error?
        raw_response.raise_for_status()

        # All seems OK, but maybe the server returned an error? If so, try to pass on as much
        # information as we can.
        response_text: str = raw_response.text
        response: typing.Dict[str, typing.Any] = json.loads(response_text)

        # Did we get sufficiently up-to-date information? It must be from the last slot we saw or a
        # newer slot.
        #
        # Only do this check if we're using a commitment level of 'processed'.
        if len(params) > 1 and "commitment" in params[1] and params[1]["commitment"] == Processed:
            if "result" in response and isinstance(response["result"], Mapping) and "context" in response["result"] and isinstance(response["result"]["context"], Mapping) and "slot" in response["result"]["context"]:
                slot: int = response["result"]["context"]["slot"]
                self._logger.debug(f"{method}() data is from slot: {slot}")
                if not self.slot_holder.is_acceptable(slot):
                    self._logger.warning(
                        f"Result is from slot: {slot} - latest slot is: {self.slot_holder.latest_slot}")
                    raise StaleSlotException(self.name, self.cluster_url, self.slot_holder.latest_slot, slot)

        if "error" in response:
            if response["error"] is str:
                message: str = typing.cast(str, response["error"])
                raise ClientException(f"Transaction failed: '{message}'", self.name, self.cluster_url)
            else:
                error = response["error"]
                error_message: str = error["message"] if "message" in error else "No message"
                error_data: typing.Dict[str, typing.Any] = error["data"] if "data" in error else {}
                error_accounts = error_data["accounts"] if "accounts" in error_data else "No accounts"
                error_code: int = error["code"] if "code" in error else -1
                error_err = error_data["err"] if "err" in error_data else "No error text returned"
                error_logs = error_data["logs"] if "logs" in error_data else "No logs"
                parameters = json.dumps({"jsonrpc": "2.0", "method": method, "params": params})

                transaction: typing.Optional[Transaction] = None
                blockhash: typing.Optional[Blockhash] = None
                if method == "sendTransaction":
                    transaction = Transaction.deserialize(b64decode(params[0]))
                    blockhash = transaction.recent_blockhash

                if error_code == -32005:
                    slots_behind: int = error["data"]["numSlotsBehind"] if "numSlotsBehind" in error["data"] else -1
                    raise NodeIsBehindException(self.name, self.cluster_url, slots_behind)

                if error_err == "BlockhashNotFound":
                    raise BlockhashNotFoundException(self.name, self.cluster_url, blockhash)

                if error_err == "AlreadyProcessed":
                    raise TransactionAlreadyProcessedException(error_message, self.name, self.cluster_url)

                exception_message: str = f"Transaction failed with: '{error_message}'"
                raise TransactionException(transaction, exception_message, error_code, self.name,
                                           self.cluster_url, method, parameters, response_text, error_accounts,
                                           error_err, error_logs, self.instruction_reporter)

        if method == "getRecentBlockhash":
            self._logger.debug(f"Recent blockhash fetched: {response}")

        # The call succeeded.
        return typing.cast(RPCResponse, response)

    def __str__(self) -> str:
        return f"« RPCCaller [{self.cluster_url}] »"

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 CompoundRPCCaller class
#
# A `CompoundRPCCaller` will try multiple providers until it succeeds (or the all fail). Should only trap
# and switch provider on exceptions that show that provider is no longer at the tip of the chain.
#
class CompoundRPCCaller(HTTPProvider):
    def __init__(self, name: str, providers: typing.Sequence[RPCCaller]):
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.__providers: typing.Sequence[RPCCaller] = providers
        self.name: str = name
        self.on_provider_change: typing.Callable[[], None] = lambda: None

    @property
    def current(self) -> RPCCaller:
        return self.__providers[0]

    @property
    def all_providers(self) -> typing.Sequence[RPCCaller]:
        return self.__providers

    def shift_to_next_provider(self) -> None:
        # This is called when the current provider is raising errors, when the next provider might not.
        # Typical RPC host errors are trapped and managed via make_request(), but some errors can't be
        # handled properly there. For example, BlockhashNotFound exceptions can be trapped there, but
        # the right answer is to switch to the next provider AND THEN fetch a fresh blockhash and retry
        # the transaction. That's not possible to do atomically (without a lot of nasty, fragile work) so
        # it's better to handle it at the higher level. That's what this method allows - the higher level
        # can call this to switch to the next provider, and it can then fetch the fresh blockhash and
        # resubmit the transaction.
        if len(self.__providers) > 1:
            self.__providers = [*self.__providers[1:], *self.__providers[:1]]
            self.on_provider_change()
        self._logger.debug(f"Told to shift provider - now using: {self.__providers[0]}")

    def make_request(self, method: RPCMethod, *params: typing.Any) -> RPCResponse:
        all_exceptions: typing.List[Exception] = []
        for provider in self.__providers:
            try:
                result = provider.make_request(method, *params)
                successful_index: int = self.__providers.index(provider)
                if successful_index != 0:
                    # Rebase the providers' list so we continue to use this successful one (until it fails)
                    self.__providers = [*self.__providers[successful_index:], *self.__providers[:successful_index]]
                    self.on_provider_change()
                    self._logger.debug(f"Shifted provider - now using: {self.__providers[0]}")
                return result
            except (requests.exceptions.HTTPError,
                    RateLimitException,
                    NodeIsBehindException,
                    StaleSlotException,
                    FailedToFetchBlockhashException) as exception:
                all_exceptions += [exception]
                self._logger.info(f"Moving to next provider - {provider} gave {exception}")

        raise CompoundException(self.name, all_exceptions)

    def is_connected(self) -> bool:
        # All we need for this to be true is for one of our providers to be connected.
        for provider in self.__providers:
            if provider.is_connected():
                return True
        return False

    def __str__(self) -> str:
        return f"« CompoundRPCCaller with {len(self.__providers)} providers - current head is: {self.__providers[0]} »"

    def __repr__(self) -> str:
        return f"{self}"


# This is purely to pass `maxRetries`: 0 in the TxOpts. (solana-py doesn't currently support this but Solana does.)
class _MaxRetriesZeroClient(Client):
    def _send_raw_transaction_args(
        self, txn: typing.Union[bytes, str], opts: TxOpts
    ) -> typing.Tuple[RPCMethod, str, typing.Dict[str, typing.Union[bool, Commitment, str]]]:

        if isinstance(txn, bytes):
            txn = b64encode(txn).decode("utf-8")

        return (
            RPCMethod("sendTransaction"),
            txn,
            {
                self._skip_preflight_key: opts.skip_preflight,
                self._preflight_comm_key: opts.preflight_commitment,
                self._encoding_key: "base64",
                "maxRetries": 0  # type: ignore
            },
        )


class BetterClient:
    def __init__(self, client: Client, name: str, cluster_name: str, commitment: Commitment, skip_preflight: bool, encoding: str, blockhash_cache_duration: int, rpc_caller: CompoundRPCCaller) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.compatible_client: Client = client
        self.name: str = name
        self.cluster_name: str = cluster_name
        self.commitment: Commitment = commitment
        self.skip_preflight: bool = skip_preflight
        self.encoding: str = encoding
        self.blockhash_cache_duration: int = blockhash_cache_duration
        self.rpc_caller: CompoundRPCCaller = rpc_caller

    @staticmethod
    def from_configuration(name: str, cluster_name: str, cluster_urls: typing.Sequence[str], commitment: Commitment, skip_preflight: bool, encoding: str, blockhash_cache_duration: int, stale_data_pauses_before_retry: typing.Sequence[float], instruction_reporter: InstructionReporter) -> "BetterClient":
        slot_holder: SlotHolder = SlotHolder()
        rpc_callers: typing.List[RPCCaller] = []
        for cluster_url in cluster_urls:
            rpc_caller: RPCCaller = RPCCaller(name, cluster_url, stale_data_pauses_before_retry,
                                              slot_holder, instruction_reporter)
            rpc_callers += [rpc_caller]

        provider: CompoundRPCCaller = CompoundRPCCaller(name, rpc_callers)
        blockhash_cache: typing.Union[BlockhashCache, bool] = False
        if blockhash_cache_duration > 0:
            blockhash_cache = BlockhashCache(blockhash_cache_duration)
        client: Client = _MaxRetriesZeroClient(cluster_url, commitment=commitment, blockhash_cache=blockhash_cache)
        client._provider = provider

        def __on_provider_change() -> None:
            if client.blockhash_cache:
                # Clear out the blockhash cache on retrying
                logging.debug("Replacing client blockhash cache.")
                client.blockhash_cache = BlockhashCache(blockhash_cache_duration)
                blockhash_resp = client.get_recent_blockhash(Finalized)
                client._process_blockhash_resp(blockhash_resp, used_immediately=False)

        provider.on_provider_change = __on_provider_change

        return BetterClient(client, name, cluster_name, commitment, skip_preflight, encoding, blockhash_cache_duration, provider)

    @property
    def cluster_url(self) -> str:
        return self.rpc_caller.current.cluster_url

    @property
    def cluster_urls(self) -> typing.Sequence[str]:
        return [rpc_caller.cluster_url for rpc_caller in self.rpc_caller.all_providers]

    @property
    def instruction_reporter(self) -> InstructionReporter:
        return self.rpc_caller.current.instruction_reporter

    @property
    def stale_data_pauses_before_retry(self) -> typing.Sequence[float]:
        return self.rpc_caller.current.stale_data_pauses_before_retry

    def require_data_from_fresh_slot(self) -> None:
        self.rpc_caller.current.require_data_from_fresh_slot()

    def get_balance(self, pubkey: typing.Union[PublicKey, str], commitment: Commitment = UnspecifiedCommitment) -> Decimal:
        resolved_commitment, _ = self.__resolve_defaults(commitment)
        response = self.compatible_client.get_balance(pubkey, resolved_commitment)
        value = Decimal(response["result"]["value"])
        return value / SOL_DECIMAL_DIVISOR

    def get_account_info(self, pubkey: typing.Union[PublicKey, str], commitment: Commitment = UnspecifiedCommitment,
                         encoding: str = UnspecifiedEncoding, data_slice: typing.Optional[DataSliceOpts] = None) -> typing.Any:
        resolved_commitment, resolved_encoding = self.__resolve_defaults(commitment, encoding)
        response = self.compatible_client.get_account_info(pubkey, resolved_commitment, resolved_encoding, data_slice)
        return response["result"]

    def get_confirmed_signatures_for_address2(self, account: typing.Union[str, Keypair, PublicKey], before: typing.Optional[str] = None, until: typing.Optional[str] = None, limit: typing.Optional[int] = None) -> typing.Sequence[str]:
        response = self.compatible_client.get_confirmed_signature_for_address2(account, before, until, limit)
        return [result["signature"] for result in response["result"]]

    def get_confirmed_transaction(self, signature: str, encoding: str = "json") -> typing.Any:
        _, resolved_encoding = self.__resolve_defaults(None, encoding)
        response = self.compatible_client.get_confirmed_transaction(signature, resolved_encoding)
        return response["result"]

    def get_minimum_balance_for_rent_exemption(self, size: int, commitment: Commitment = UnspecifiedCommitment) -> int:
        resolved_commitment, _ = self.__resolve_defaults(commitment)
        response = self.compatible_client.get_minimum_balance_for_rent_exemption(size, resolved_commitment)
        return int(response["result"])

    def get_program_accounts(self, pubkey: typing.Union[str, PublicKey],
                             commitment: Commitment = UnspecifiedCommitment,
                             encoding: typing.Optional[str] = UnspecifiedEncoding,
                             data_slice: typing.Optional[DataSliceOpts] = None,
                             data_size: typing.Optional[int] = None,
                             memcmp_opts: typing.Optional[typing.List[MemcmpOpts]] = None) -> typing.Any:
        resolved_commitment, resolved_encoding = self.__resolve_defaults(commitment, encoding)
        response = self.compatible_client.get_program_accounts(
            pubkey, resolved_commitment, resolved_encoding, data_slice, data_size, memcmp_opts)
        return response["result"]

    def get_recent_blockhash(self, commitment: Commitment = UnspecifiedCommitment) -> Blockhash:
        resolved_commitment, _ = self.__resolve_defaults(commitment)
        response = self.compatible_client.get_recent_blockhash(resolved_commitment)
        return Blockhash(response["result"]["value"]["blockhash"])

    def get_token_account_balance(self, pubkey: typing.Union[str, PublicKey], commitment: Commitment = UnspecifiedCommitment) -> Decimal:
        resolved_commitment, _ = self.__resolve_defaults(commitment)
        response = self.compatible_client.get_token_account_balance(pubkey, resolved_commitment)
        value = Decimal(response["result"]["value"]["amount"])
        decimal_places = response["result"]["value"]["decimals"]
        divisor = Decimal(10 ** decimal_places)
        return value / divisor

    def get_token_accounts_by_owner(self, owner: PublicKey, token_account_options: TokenAccountOpts, commitment: Commitment = UnspecifiedCommitment,) -> typing.Any:
        resolved_commitment, _ = self.__resolve_defaults(commitment)
        response = self.compatible_client.get_token_accounts_by_owner(owner, token_account_options, resolved_commitment)
        return response["result"]["value"]

    def get_multiple_accounts(self, pubkeys: typing.List[typing.Union[PublicKey, str]], commitment: Commitment = UnspecifiedCommitment,
                              encoding: str = UnspecifiedEncoding, data_slice: typing.Optional[DataSliceOpts] = None) -> typing.Any:
        resolved_commitment, resolved_encoding = self.__resolve_defaults(commitment, encoding)
        response = self.compatible_client.get_multiple_accounts(
            pubkeys, resolved_commitment, resolved_encoding, data_slice)
        return response["result"]["value"]

    def send_transaction(self, transaction: Transaction, *signers: Keypair, opts: TxOpts = TxOpts(preflight_commitment=UnspecifiedCommitment)) -> str:
        # This method is an exception to the normal exception-handling to fail over to the next RPC provider.
        #
        # Normal RPC exceptions just move on to the next RPC provider and try again. That won't work with the
        # BlockhashNotFoundException, since a stale blockhash will be stale for all providers and it probably
        # indicates a problem with the current node returning the stale blockhash anyway.
        #
        # What we want to do in this situation is: retry the same transaction (which we know for certain failed)
        # but retry it with the next provider in the list, with a fresh recent_blockhash. (Setting the transaction's
        # recent_blockhash to None makes the client fetch a fresh one.)
        last_exception: BlockhashNotFoundException
        for provider in self.rpc_caller.all_providers:
            try:
                proper_commitment: Commitment = opts.preflight_commitment
                proper_skip_preflight = opts.skip_preflight
                if proper_commitment == UnspecifiedCommitment:
                    proper_commitment = self.commitment
                    proper_skip_preflight = self.skip_preflight

                proper_opts = TxOpts(preflight_commitment=proper_commitment,
                                     skip_confirmation=opts.skip_confirmation,
                                     skip_preflight=proper_skip_preflight)

                response = self.compatible_client.send_transaction(transaction, *signers, opts=proper_opts)
                signature: str = str(response["result"])

                if signature != _STUB_TRANSACTION_SIGNATURE:
                    transaction_status = self.compatible_client.get_signature_statuses([signature])
                    if "result" in transaction_status and "context" in transaction_status["result"] and "slot" in transaction_status["result"]["context"]:
                        slot: int = transaction_status["result"]["context"]["slot"]
                        self.rpc_caller.current.require_data_from_fresh_slot(slot)
                    else:
                        self._logger.error(f"Could not get status for signature {signature}")
                else:
                    self._logger.error("Could not get status for stub signature")

                return signature
            except BlockhashNotFoundException as blockhash_not_found_exception:
                self._logger.debug(
                    f"Trying next provider after intercepting blockhash exception on provider {provider}: {blockhash_not_found_exception}")
                last_exception = blockhash_not_found_exception
                transaction.recent_blockhash = None
                self.rpc_caller.shift_to_next_provider()

        raise last_exception

    def wait_for_confirmation(self, transaction_ids: typing.Sequence[str], max_wait_in_seconds: int = 60) -> typing.Sequence[str]:
        self._logger.info(f"Waiting up to {max_wait_in_seconds} seconds for {transaction_ids}.")
        all_confirmed: typing.List[str] = []
        start_time: datetime.datetime = datetime.datetime.now()
        cutoff: datetime.datetime = start_time + datetime.timedelta(seconds=max_wait_in_seconds)
        for transaction_id in transaction_ids:
            while datetime.datetime.now() < cutoff:
                time.sleep(1)
                confirmed = self.get_confirmed_transaction(transaction_id)
                if confirmed is not None:
                    self._logger.info(
                        f"Confirmed {transaction_id} after {datetime.datetime.now() - start_time} seconds.")
                    all_confirmed += [transaction_id]
                    break

        if len(all_confirmed) != len(transaction_ids):
            self._logger.info(f"Timed out after {max_wait_in_seconds} seconds waiting on transaction {transaction_id}.")
        return all_confirmed

    def __resolve_defaults(self, commitment: typing.Optional[Commitment], encoding: typing.Optional[str] = None) -> typing.Tuple[Commitment, str]:
        if commitment is None or commitment == UnspecifiedCommitment:
            commitment = self.commitment

        if encoding is None or encoding == UnspecifiedEncoding:
            encoding = self.encoding

        return commitment, encoding

    def __str__(self) -> str:
        return f"« BetterClient [{self.cluster_name}]: {self.cluster_urls} »"

    def __repr__(self) -> str:
        return f"{self}"
