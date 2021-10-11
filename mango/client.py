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

import collections
import datetime
import itertools
import json
import logging
import requests
import time
import typing


from base64 import b64encode
from decimal import Decimal
from solana.blockhash import Blockhash
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.rpc.commitment import Commitment
from solana.rpc.types import DataSliceOpts, MemcmpOpts, RPCResponse, TokenAccountOpts, TxOpts
from solana.transaction import Transaction

from .constants import SOL_DECIMAL_DIVISOR
from .instructionreporter import InstructionReporter


# # 🥭 ClientException class
#
# A `ClientException` exception base class that allows trapping and handling rate limiting
# independent of other error handling.
#
class ClientException(Exception):
    def __init__(self, message: str, name: str, cluster_url: str):
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
    def __init__(self, name: str, cluster_url: str, blockhash: typing.Optional[Blockhash] = None):
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
    def __init__(self, name: str, cluster_url: str, slots_behind: int):
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
    def __init__(self, message: str, name: str, cluster_url: str, pauses: typing.Sequence[float]):
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
    def __init__(self, transaction: typing.Optional[Transaction], message: str, code: int, name: str, cluster_url: str, rpc_method: str, request_text: str, response_text: str, accounts: typing.Union[str, typing.List[str], None], errors: typing.Union[str, typing.List[str], None], logs: typing.Union[str, typing.List[str], None], instruction_reporter: InstructionReporter = InstructionReporter()):
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
        self.accounts: typing.List[str] = _ensure_list(accounts)
        self.errors: typing.List[str] = _ensure_list(errors)
        self.logs: typing.List[str] = _ensure_list(logs)
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


_CommitmentKey = "commitment"
_EncodingKey = "encoding"
_FiltersKey = "filters"
_DataSliceKey = "dataSlice"
_DataSizeKey = "dataSize"
_MemCmp = "memcmp"
_SkipPreflightKey = "skipPreflight"
_PreflightCommitmentKey = "preflightCommitment"

UnspecifiedCommitment = Commitment("unspecified")
UnspecifiedEncoding = "unspecified"


class CachedBlockhash(typing.NamedTuple):
    blockhash: Blockhash
    timestamp: datetime.datetime

    def viable(self, cache_window: datetime.timedelta) -> bool:
        expiration: datetime.datetime = self.timestamp + cache_window
        if datetime.datetime.now() < expiration:
            return True
        return False


# # 🥭 CompatibleClient class
#
# A `CompatibleClient` class that tries to be compatible with the proper Solana Client, but that handles
# some common operations better from our point of view.
#
class CompatibleClient(Client):
    def __init__(self, name: str, cluster_name: str, cluster_url: str, commitment: Commitment, blockhash_commitment: Commitment, skip_preflight: bool, encoding: str, blockhash_cache_duration: datetime.timedelta, instruction_reporter: InstructionReporter):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.name: str = name
        self.cluster_name: str = cluster_name
        self.cluster_url: str = cluster_url
        self.commitment: Commitment = commitment
        self.blockhash_commitment: Commitment = blockhash_commitment
        self.skip_preflight: bool = skip_preflight
        self.encoding: str = encoding
        self.blockhash_cache_duration: datetime.timedelta = blockhash_cache_duration
        self.instruction_reporter: InstructionReporter = instruction_reporter

        self._request_counter = itertools.count()
        self._cached_blockhash: CachedBlockhash = CachedBlockhash(Blockhash("unset"), datetime.datetime.min)

        # Keep a note of the last 10 blockhashes, if we're using caching
        self._previous_blockhashes: collections.deque = collections.deque([], 10)

    def is_node_healthy(self) -> bool:
        try:
            response = requests.get(f"{self.cluster_url}/health")
            response.raise_for_status()
        except (IOError, requests.HTTPError) as err:
            self.logger.warning(f"[{self.name}] Health check failed with error: {err}")
            return False

        return response.ok

    def get_balance(self, pubkey: typing.Union[PublicKey, str], commitment: typing.Optional[Commitment] = UnspecifiedCommitment) -> RPCResponse:
        options = self._build_options(commitment, None, None)
        return self._send_request("getBalance", str(pubkey), options)

    def get_sol_balance(self, account_public_key: PublicKey) -> Decimal:
        result = self.get_balance(account_public_key)
        value = Decimal(result["result"]["value"])
        return value / SOL_DECIMAL_DIVISOR

    def get_account_info(self, pubkey: typing.Union[PublicKey, str], commitment: typing.Optional[Commitment] = UnspecifiedCommitment,
                         encoding: str = UnspecifiedEncoding, data_slice: typing.Optional[DataSliceOpts] = None) -> RPCResponse:
        options = self._build_options_with_encoding(commitment, encoding, data_slice)
        return self._send_request("getAccountInfo", str(pubkey), options)

    def get_confirmed_signature_for_address2(self, account: typing.Union[str, Keypair, PublicKey], before: typing.Optional[str] = None, limit: typing.Optional[int] = None) -> RPCResponse:
        if isinstance(account, Keypair):
            account = str(account.public_key)

        if isinstance(account, PublicKey):
            account = str(account)

        opts: typing.Dict[str, typing.Union[int, str]] = {}
        if before:
            opts["before"] = before

        if limit:
            opts["limit"] = limit

        return self._send_request("getConfirmedSignaturesForAddress2", account, opts)

    def get_confirmed_transaction(self, signature: str, encoding: str = "json") -> RPCResponse:
        return self._send_request("getConfirmedTransaction", signature, encoding)

    def get_minimum_balance_for_rent_exemption(self, size: int, commitment: typing.Optional[Commitment] = UnspecifiedCommitment) -> RPCResponse:
        options = self._build_options(commitment, None, None)
        return self._send_request("getMinimumBalanceForRentExemption", size, options)

    def get_program_accounts(self, pubkey: typing.Union[str, PublicKey],
                             commitment: typing.Optional[Commitment] = UnspecifiedCommitment,
                             encoding: typing.Optional[str] = UnspecifiedEncoding,
                             data_slice: typing.Optional[DataSliceOpts] = None,
                             data_size: typing.Optional[int] = None,
                             memcmp_opts: typing.Optional[typing.List[MemcmpOpts]] = None) -> RPCResponse:
        options = self._build_options_with_encoding(commitment, encoding, data_slice)
        options[_FiltersKey] = []

        if data_size:
            options[_FiltersKey].append({_DataSizeKey: data_size})

        for memcmps in [] if not memcmp_opts else memcmp_opts:
            options[_FiltersKey].append({_MemCmp: dict(memcmps._asdict())})

        return self._send_request("getProgramAccounts", str(pubkey), options)

    def get_recent_blockhash(self, commitment: typing.Optional[Commitment] = UnspecifiedCommitment) -> RPCResponse:
        options = self._build_options(commitment, None, None)
        return self._send_request("getRecentBlockhash", options)

    def get_fresh_recent_blockhash(self, commitment: typing.Optional[Commitment] = UnspecifiedCommitment) -> Blockhash:
        # Last one should be zero so we're not pausing when we're not retrying.
        pauses: typing.Sequence[float] = [0.1, 0.2, 0.4, 0.5, 0]
        for pause in pauses:
            blockhash_resp = self.get_recent_blockhash(commitment)
            if blockhash_resp["result"]:
                blockhash = Blockhash(blockhash_resp["result"]["value"]["blockhash"])
                if blockhash not in self._previous_blockhashes:
                    self._previous_blockhashes.append(blockhash)
                    return blockhash
            time.sleep(pause)

        raise FailedToFetchBlockhashException(
            f"Failed to get fresh recent blockhash after {len(pauses)} attempts.", self.name, self.cluster_url, pauses)

    def get_cached_recent_blockhash(self, commitment: typing.Optional[Commitment] = UnspecifiedCommitment) -> Blockhash:
        if self.blockhash_cache_duration.total_seconds() == 0:
            blockhash_resp = self.get_recent_blockhash(commitment)
            if not blockhash_resp["result"]:
                raise FailedToFetchBlockhashException(
                    "Failed to get recent blockhash.", self.name, self.cluster_url, [])
            return Blockhash(blockhash_resp["result"]["value"]["blockhash"])

        if not self._cached_blockhash.viable(self.blockhash_cache_duration):
            blockhash: Blockhash = self.get_fresh_recent_blockhash(commitment)
            self._cached_blockhash = CachedBlockhash(blockhash=blockhash, timestamp=datetime.datetime.now())
        return self._cached_blockhash.blockhash

    def get_token_account_balance(self, pubkey: typing.Union[str, PublicKey], commitment: typing.Optional[Commitment] = UnspecifiedCommitment):
        options = self._build_options(commitment, None, None)
        return self._send_request("getTokenAccountBalance", str(pubkey), options)

    def get_token_accounts_by_owner(self, owner: PublicKey, token_account_options: TokenAccountOpts, commitment: typing.Optional[Commitment] = UnspecifiedCommitment,) -> RPCResponse:
        options = self._build_options_with_encoding(
            commitment, token_account_options.encoding, token_account_options.data_slice)

        if not token_account_options.mint and not token_account_options.program_id:
            raise ValueError("Please provide one of mint or program_id")

        account_options: typing.Dict[str, str] = {}
        if token_account_options.mint:
            account_options["mint"] = str(token_account_options.mint)
        if token_account_options.program_id:
            account_options["programId"] = str(token_account_options.program_id)

        return self._send_request("getTokenAccountsByOwner", str(owner), account_options, options)

    def get_multiple_accounts(self, pubkeys: typing.Sequence[typing.Union[PublicKey, str]], commitment: typing.Optional[Commitment] = UnspecifiedCommitment,
                              encoding: str = UnspecifiedEncoding, data_slice: typing.Optional[DataSliceOpts] = None) -> RPCResponse:
        options = self._build_options_with_encoding(commitment, encoding, data_slice)
        pubkey_strings: typing.Sequence[str] = list([str(pubkey) for pubkey in pubkeys])
        return self._send_request("getMultipleAccounts", pubkey_strings, options)

    def send_transaction(self, txn: Transaction, *signers: Keypair, opts: TxOpts = TxOpts(preflight_commitment=UnspecifiedCommitment), recent_blockhash: typing.Optional[Blockhash] = None) -> RPCResponse:
        if recent_blockhash is None:
            recent_blockhash = self.get_cached_recent_blockhash(self.blockhash_commitment)
        txn.recent_blockhash = recent_blockhash
        txn.sign(*signers)

        encoded_transaction: str = b64encode(txn.serialize()).decode("utf-8")

        commitment: Commitment = opts.preflight_commitment
        if commitment == UnspecifiedCommitment:
            commitment = self.commitment

        skip_preflight: bool = opts.skip_preflight or self.skip_preflight
        encoding: str = self.encoding
        if encoding == "base64+zstd":
            # sendTransaction() only supports base64 and base58, according to the docs:
            #    https://docs.solana.com/developing/clients/jsonrpc-api#sendtransaction
            # The error implies it accepts more:
            #    Invalid params: unknown variant `base64+zstd`, expected one of `binary`, `base64`, `base58`, `json`, `jsonParsed`.
            # but even that list doesn't accept base64+zstd.
            encoding = "base64"

        response = self._send_request(
            "sendTransaction",
            encoded_transaction,
            {
                _SkipPreflightKey: skip_preflight,
                _PreflightCommitmentKey: commitment,
                _EncodingKey: encoding
            },
            transaction=txn,
            blockhash=txn.recent_blockhash
        )

        if ("id" in response) and ("result" in response):
            self.logger.debug(f"Transaction signature[{response['id']}]: {response['result']}")

        return response

    # def _send_request(self, method: str, transaction: typing.Optional[Transaction] = None, blockhash: typing.Optional[Blockhash] = None, *params: typing.Any) -> RPCResponse:
    def _send_request(self, method: str, *args: typing.Any, **kwargs) -> RPCResponse:
        request_id = next(self._request_counter) + 1
        headers = {"Content-Type": "application/json"}
        data = json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": args})
        raw_response = requests.post(self.cluster_url, headers=headers, data=data)

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
        response: typing.Dict = json.loads(response_text)
        if "error" in response:
            if response["error"] is str:
                message: str = typing.cast(str, response["error"])
                raise ClientException(f"Transaction failed: '{message}'", self.name, self.cluster_url)
            else:
                error_message: str = response["error"]["message"] if "message" in response["error"] else "No message"
                exception_message: str = f"Transaction failed with: '{error_message}'"
                error_code: int = response["error"]["code"] if "code" in response["error"] else -1
                if error_code == -32005:
                    slots_behind: int = response["error"]["data"]["numSlotsBehind"] if "numSlotsBehind" in response["error"]["data"] else -1
                    raise NodeIsBehindException(self.name, self.cluster_url, slots_behind)
                error_data: typing.Dict = response["error"]["data"] if "data" in response["error"] else {}
                error_accounts = error_data["accounts"] if "accounts" in error_data else "No accounts"
                error_err = error_data["err"] if "err" in error_data else "No error text returned"
                if error_err == "BlockhashNotFound":
                    blockhash: typing.Optional[Blockhash] = kwargs["blockhash"] if "blockhash" in kwargs else None
                    raise BlockhashNotFoundException(self.name, self.cluster_url, blockhash)
                error_logs = error_data["logs"] if "logs" in error_data else "No logs"
                transaction: typing.Optional[Transaction] = kwargs["transaction"] if "transaction" in kwargs else None
                raise TransactionException(transaction, exception_message, error_code, self.name, self.cluster_url,
                                           method, data, response_text, error_accounts, error_err, error_logs)

        # The call succeeded.
        return typing.cast(RPCResponse, response)

    def _build_options(self, commitment: typing.Optional[Commitment], encoding: typing.Optional[str], data_slice: typing.Optional[DataSliceOpts]) -> typing.Dict[str, typing.Any]:
        options: typing.Dict[str, typing.Any] = {}
        if commitment is None or commitment == UnspecifiedCommitment:
            options[_CommitmentKey] = self.commitment
        else:
            options[_CommitmentKey] = commitment

        if encoding:
            options[_EncodingKey] = encoding

        if data_slice:
            options[_DataSliceKey] = dict(data_slice._asdict())

        return options

    def _build_options_with_encoding(self, commitment: typing.Optional[Commitment], encoding: typing.Optional[str], data_slice: typing.Optional[DataSliceOpts]) -> typing.Dict[str, typing.Any]:
        encoding_to_use: str = self.encoding
        if (encoding is not None) and (encoding != UnspecifiedEncoding):
            encoding_to_use = encoding
        return self._build_options(commitment, encoding_to_use, data_slice)

    def __str__(self) -> str:
        return f"« 𝙲𝚘𝚖𝚙𝚊𝚝𝚒𝚋𝚕𝚎𝙲𝚕𝚒𝚎𝚗𝚝 [{self.cluster_name}]: {self.cluster_url} »"

    def __repr__(self) -> str:
        return f"{self}"


class BetterClient:
    def __init__(self, client: CompatibleClient):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.compatible_client: CompatibleClient = client

        # kangda said in Discord: https://discord.com/channels/791995070613159966/836239696467591186/847816026245693451
        # "I think you are better off doing 4,8,16,20,30"
        self.retry_pauses: typing.Sequence[Decimal] = [Decimal(4), Decimal(
            8), Decimal(16), Decimal(20), Decimal(30)]

    @property
    def cluster_name(self) -> str:
        return self.compatible_client.cluster_name

    @cluster_name.setter
    def cluster_name(self, value: str) -> None:
        self.compatible_client.cluster_name = value

    @property
    def cluster_url(self) -> str:
        return self.compatible_client.cluster_url

    @cluster_url.setter
    def cluster_url(self, value: str) -> None:
        self.compatible_client.cluster_url = value

    @property
    def encoding(self) -> str:
        return self.compatible_client.encoding

    @encoding.setter
    def encoding(self, value: str) -> None:
        self.compatible_client.encoding = value

    @property
    def commitment(self) -> Commitment:
        return self.compatible_client.commitment

    @commitment.setter
    def commitment(self, value: Commitment) -> None:
        self.compatible_client.commitment = value

    @property
    def blockhash_commitment(self) -> Commitment:
        return self.compatible_client.blockhash_commitment

    @blockhash_commitment.setter
    def blockhash_commitment(self, value: Commitment) -> None:
        self.compatible_client.blockhash_commitment = value

    @property
    def skip_preflight(self) -> bool:
        return self.compatible_client.skip_preflight

    @skip_preflight.setter
    def skip_preflight(self, value: bool) -> None:
        self.compatible_client.skip_preflight = value

    @property
    def instruction_reporter(self) -> InstructionReporter:
        return self.compatible_client.instruction_reporter

    @instruction_reporter.setter
    def instruction_reporter(self, value: InstructionReporter) -> None:
        self.compatible_client.instruction_reporter = value

    @staticmethod
    def from_configuration(name: str, cluster_name: str, cluster_url: str, commitment: Commitment, blockhash_commitment: Commitment, skip_preflight: bool, encoding: str, blockhash_cache_duration: datetime.timedelta, instruction_reporter: InstructionReporter) -> "BetterClient":
        compatible = CompatibleClient(name, cluster_name, cluster_url, commitment, blockhash_commitment, skip_preflight,
                                      encoding, blockhash_cache_duration, instruction_reporter)
        return BetterClient(compatible)

    def is_node_healthy(self) -> bool:
        return self.compatible_client.is_node_healthy()

    def get_balance(self, pubkey: typing.Union[PublicKey, str], commitment: Commitment = UnspecifiedCommitment) -> Decimal:
        response = self.compatible_client.get_balance(pubkey, commitment)
        value = Decimal(response["result"]["value"])
        return value / SOL_DECIMAL_DIVISOR

    def get_account_info(self, pubkey: typing.Union[PublicKey, str], commitment: Commitment = UnspecifiedCommitment,
                         encoding: str = UnspecifiedEncoding, data_slice: typing.Optional[DataSliceOpts] = None) -> typing.Dict:
        response = self.compatible_client.get_account_info(pubkey, commitment, encoding, data_slice)
        return response["result"]

    def get_confirmed_signatures_for_address2(self, account: typing.Union[str, Keypair, PublicKey], before: typing.Optional[str] = None, limit: typing.Optional[int] = None) -> typing.Sequence[str]:
        response = self.compatible_client.get_confirmed_signature_for_address2(account, before, limit)
        return [result["signature"] for result in response["result"]]

    def get_confirmed_transaction(self, signature: str, encoding: str = "json") -> typing.Dict:
        response = self.compatible_client.get_confirmed_transaction(signature, encoding)
        return response["result"]

    def get_minimum_balance_for_rent_exemption(self, size: int, commitment: Commitment = UnspecifiedCommitment) -> int:
        response = self.compatible_client.get_minimum_balance_for_rent_exemption(size, commitment)
        return response["result"]

    def get_program_accounts(self, pubkey: typing.Union[str, PublicKey],
                             commitment: Commitment = UnspecifiedCommitment,
                             encoding: typing.Optional[str] = UnspecifiedEncoding,
                             data_slice: typing.Optional[DataSliceOpts] = None,
                             data_size: typing.Optional[int] = None,
                             memcmp_opts: typing.Optional[typing.List[MemcmpOpts]] = None) -> typing.Dict:
        response = self.compatible_client.get_program_accounts(
            pubkey, commitment, encoding, data_slice, data_size, memcmp_opts)
        return response["result"]

    def get_recent_blockhash(self, commitment: Commitment = UnspecifiedCommitment) -> Blockhash:
        response = self.compatible_client.get_recent_blockhash(commitment)
        return Blockhash(response["result"]["value"]["blockhash"])

    def get_token_account_balance(self, pubkey: typing.Union[str, PublicKey], commitment: Commitment = UnspecifiedCommitment) -> Decimal:
        response = self.compatible_client.get_token_account_balance(pubkey, commitment)
        value = Decimal(response["result"]["value"]["amount"])
        decimal_places = response["result"]["value"]["decimals"]
        divisor = Decimal(10 ** decimal_places)
        return value / divisor

    def get_token_accounts_by_owner(self, owner: PublicKey, token_account_options: TokenAccountOpts, commitment: Commitment = UnspecifiedCommitment,) -> typing.Sequence[typing.Dict]:
        response = self.compatible_client.get_token_accounts_by_owner(owner, token_account_options, commitment)
        return response["result"]["value"]

    def get_multiple_accounts(self, pubkeys: typing.Sequence[PublicKey], commitment: Commitment = UnspecifiedCommitment,
                              encoding: str = UnspecifiedEncoding, data_slice: typing.Optional[DataSliceOpts] = None) -> typing.Sequence[typing.Dict]:
        response = self.compatible_client.get_multiple_accounts(pubkeys, commitment, encoding, data_slice)
        return response["result"]["value"]

    def send_transaction(self, transaction: Transaction, *signers: Keypair, opts: TxOpts = TxOpts(preflight_commitment=UnspecifiedCommitment)) -> str:
        response = self.compatible_client.send_transaction(
            transaction, *signers, opts=opts)
        return response["result"]

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

    def __str__(self) -> str:
        return f"« 𝙱𝚎𝚝𝚝𝚎𝚛𝙲𝚕𝚒𝚎𝚗𝚝 [{self.cluster_name}]: {self.cluster_url} »"

    def __repr__(self) -> str:
        return f"{self}"
