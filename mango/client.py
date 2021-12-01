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


from base64 import b64decode
from decimal import Decimal
from solana.blockhash import Blockhash, BlockhashCache
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.rpc.commitment import Commitment
from solana.rpc.providers.http import HTTPProvider
from solana.rpc.types import DataSliceOpts, MemcmpOpts, RPCMethod, RPCResponse, TokenAccountOpts, TxOpts
from solana.transaction import Transaction

from .constants import SOL_DECIMAL_DIVISOR
from .instructionreporter import InstructionReporter
from .logmessages import expand_log_messages


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
            instruction_details = "\n".join(list(map(self.instruction_reporter.report, self.transaction.instructions)))
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
        return f"""« 𝚃𝚛𝚊𝚗𝚜𝚊𝚌𝚝𝚒𝚘𝚗𝙴𝚡𝚌𝚎𝚙𝚝𝚒𝚘𝚗 in '{self.name}' [{self.rpc_method}]: {self.code}:: {self.message}{transaction_details}
    Accounts:
        {accounts}
    Errors:
        {errors}
    Logs:
        {logs}{request_details}{response_details}
»"""

    def __repr__(self) -> str:
        return f"{self}"


UnspecifiedCommitment = Commitment("unspecified")
UnspecifiedEncoding = "unspecified"


# # 🥭 ErrorHandlingProvider class
#
# A `ErrorHandlingProvider` extends the HTTPProvider with better error handling.
#
class ErrorHandlingProvider(HTTPProvider):
    def __init__(self, name: str, cluster_url: str, instruction_reporter: InstructionReporter):
        super().__init__(cluster_url)
        self.name: str = name
        self.cluster_url: str = cluster_url
        self.instruction_reporter: InstructionReporter = instruction_reporter

    def make_request(self, method: RPCMethod, *params: typing.Any) -> RPCResponse:
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

                exception_message: str = f"Transaction failed with: '{error_message}'"
                raise TransactionException(transaction, exception_message, error_code, self.name,
                                           self.cluster_url, method, parameters, response_text, error_accounts,
                                           error_err, error_logs, self.instruction_reporter)

        # The call succeeded.
        return typing.cast(RPCResponse, response)


class BetterClient:
    def __init__(self, client: Client, name: str, cluster_name: str, cluster_url: str, commitment: Commitment, skip_preflight: bool, encoding: str, blockhash_cache_duration: int, instruction_reporter: InstructionReporter) -> None:
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.compatible_client: Client = client
        self.name: str = name
        self.cluster_name: str = cluster_name
        self.cluster_url: str = cluster_url
        self.commitment: Commitment = commitment
        self.skip_preflight: bool = skip_preflight
        self.encoding: str = encoding
        self.blockhash_cache_duration: int = blockhash_cache_duration
        self.instruction_reporter: InstructionReporter = instruction_reporter

        # kangda said in Discord: https://discord.com/channels/791995070613159966/836239696467591186/847816026245693451
        # "I think you are better off doing 4,8,16,20,30"
        self.retry_pauses: typing.Sequence[Decimal] = [Decimal(4), Decimal(
            8), Decimal(16), Decimal(20), Decimal(30)]

    @staticmethod
    def from_configuration(name: str, cluster_name: str, cluster_url: str, commitment: Commitment, skip_preflight: bool, encoding: str, blockhash_cache_duration: int, instruction_reporter: InstructionReporter) -> "BetterClient":
        provider: HTTPProvider = ErrorHandlingProvider(name, cluster_url, instruction_reporter)
        blockhash_cache: typing.Union[BlockhashCache, bool] = False
        if blockhash_cache_duration > 0:
            blockhash_cache = BlockhashCache(blockhash_cache_duration)
        client: Client = Client(cluster_url, commitment=commitment, blockhash_cache=blockhash_cache)
        client._provider = provider

        return BetterClient(client, name, cluster_name, cluster_url, commitment, skip_preflight, encoding, blockhash_cache_duration, instruction_reporter)

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
        proper_commitment: Commitment = opts.preflight_commitment
        if proper_commitment == UnspecifiedCommitment:
            proper_commitment = self.commitment

        proper_opts = TxOpts(preflight_commitment=proper_commitment,
                             skip_confirmation=opts.skip_confirmation,
                             skip_preflight=opts.skip_preflight)

        response = self.compatible_client.send_transaction(transaction, *signers, opts=proper_opts)
        return str(response["result"])

    def wait_for_confirmation(self, transaction_ids: typing.Sequence[str], max_wait_in_seconds: int = 60) -> typing.Sequence[str]:
        self.logger.info(f"Waiting up to {max_wait_in_seconds} seconds for {transaction_ids}.")
        all_confirmed: typing.List[str] = []
        start_time: datetime.datetime = datetime.datetime.now()
        cutoff: datetime.datetime = start_time + datetime.timedelta(seconds=max_wait_in_seconds)
        for transaction_id in transaction_ids:
            while datetime.datetime.now() < cutoff:
                time.sleep(1)
                confirmed = self.get_confirmed_transaction(transaction_id)
                if confirmed is not None:
                    self.logger.info(
                        f"Confirmed {transaction_id} after {datetime.datetime.now() - start_time} seconds.")
                    all_confirmed += [transaction_id]
                    break

        if len(all_confirmed) != len(transaction_ids):
            self.logger.info(f"Timed out after {max_wait_in_seconds} seconds waiting on transaction {transaction_id}.")
        return all_confirmed

    def __resolve_defaults(self, commitment: typing.Optional[Commitment], encoding: typing.Optional[str] = None) -> typing.Tuple[Commitment, str]:
        if commitment is None or commitment == UnspecifiedCommitment:
            commitment = self.commitment

        if encoding is None or encoding == UnspecifiedEncoding:
            encoding = self.encoding

        return commitment, encoding

    def __str__(self) -> str:
        return f"« 𝙱𝚎𝚝𝚝𝚎𝚛𝙲𝚕𝚒𝚎𝚗𝚝 [{self.cluster_name}]: {self.cluster_url} »"

    def __repr__(self) -> str:
        return f"{self}"
