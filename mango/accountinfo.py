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


import logging
import time
import typing

from decimal import Decimal
from solana.publickey import PublicKey
from solana.rpc.types import RPCResponse

from .context import Context
from .encoding import decode_binary, encode_binary


# # 🥭 AccountInfo class
#


class AccountInfo:
    def __init__(self, address: PublicKey, executable: bool, lamports: Decimal, owner: PublicKey, rent_epoch: Decimal, data: bytes):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.address: PublicKey = address
        self.executable: bool = executable
        self.lamports: Decimal = lamports
        self.owner: PublicKey = owner
        self.rent_epoch: Decimal = rent_epoch
        self.data: bytes = data

    def encoded_data(self) -> typing.List:
        return encode_binary(self.data)

    def __str__(self) -> str:
        return f"""« AccountInfo [{self.address}]:
    Owner: {self.owner}
    Executable: {self.executable}
    Lamports: {self.lamports}
    Rent Epoch: {self.rent_epoch}
»"""

    def __repr__(self) -> str:
        return f"{self}"

    @staticmethod
    def load(context: Context, address: PublicKey) -> typing.Optional["AccountInfo"]:
        result: typing.Optional[typing.Dict[str, typing.Any]] = context.client.get_account_info(address)
        if result is None or result["value"] is None:
            return None

        return AccountInfo._from_response_values(result["value"], address)

    @staticmethod
    def load_multiple(context: Context, addresses: typing.List[PublicKey], chunk_size: int = 100, sleep_between_calls: float = 0.0) -> typing.List["AccountInfo"]:
        # This is a tricky one to get right.
        # Some errors this can generate:
        #  413 Client Error: Payload Too Large for url
        #  Error response from server: 'Too many inputs provided; max 100', code: -32602
        address_strings: typing.List[str] = list(map(PublicKey.__str__, addresses))
        multiple: typing.List[AccountInfo] = []
        chunks = AccountInfo._split_list_into_chunks(address_strings, chunk_size)
        for counter, chunk in enumerate(chunks):
            result: typing.Sequence[typing.Dict] = context.client.get_multiple_accounts(chunk)
            response_value_list = zip(result, addresses)
            multiple += list(map(lambda pair: AccountInfo._from_response_values(pair[0], pair[1]), response_value_list))
            if (sleep_between_calls > 0.0) and (counter < (len(chunks) - 1)):
                time.sleep(sleep_between_calls)

        return multiple

    @staticmethod
    def _from_response_values(response_values: typing.Dict[str, typing.Any], address: PublicKey) -> "AccountInfo":
        executable = bool(response_values["executable"])
        lamports = Decimal(response_values["lamports"])
        owner = PublicKey(response_values["owner"])
        rent_epoch = Decimal(response_values["rentEpoch"])
        data = decode_binary(response_values["data"])
        return AccountInfo(address, executable, lamports, owner, rent_epoch, data)

    @staticmethod
    def from_response(response: RPCResponse, address: PublicKey) -> "AccountInfo":
        return AccountInfo._from_response_values(response["result"]["value"], address)

    @staticmethod
    def _split_list_into_chunks(to_chunk: typing.List, chunk_size: int = 100) -> typing.List[typing.List]:
        chunks = []
        start = 0
        while start < len(to_chunk):
            chunk = to_chunk[start:start + chunk_size]
            chunks += [chunk]
            start += chunk_size
        return chunks
