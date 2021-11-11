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
import typing

from decimal import Decimal
from solana.publickey import PublicKey

from .cache import RootBankCache, Cache
from .context import Context
from .instrumentlookup import InstrumentLookup
from .rootbank import NodeBank, RootBank
from .token import Instrument, Token


# # 🥭 TokenInfo class
#
# `TokenInfo` defines additional information for a `Token`.
#
class TokenInfo():
    def __init__(self, token: Token, root_bank_address: PublicKey) -> None:
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.token: Token = token
        self.root_bank_address: PublicKey = root_bank_address

    @staticmethod
    def from_layout_or_none(layout: typing.Any, instrument_lookup: InstrumentLookup) -> typing.Optional["TokenInfo"]:
        if layout.mint is None:
            return None

        instrument: typing.Optional[Instrument] = instrument_lookup.find_by_mint(layout.mint)
        if instrument is None:
            raise Exception(f"Token with mint {layout.mint} could not be found.")
        token: Token = Token.ensure(instrument)
        root_bank_address: PublicKey = layout.root_bank
        decimals: Decimal = layout.decimals

        if decimals != token.decimals:
            raise Exception(
                f"Conflict between number of decimals in token static data {token.decimals} and group {decimals} for token {token.symbol}.")

        return TokenInfo(token, root_bank_address)

    @staticmethod
    def find_by_symbol(values: typing.Sequence[typing.Optional["TokenInfo"]], symbol: str) -> "TokenInfo":
        found = [
            value for value in values if value is not None and value.token is not None and value.token.symbol_matches(symbol)]
        if len(found) == 0:
            raise Exception(f"Token '{symbol}' not found in token infos: {values}")

        if len(found) > 1:
            raise Exception(f"Token '{symbol}' matched multiple tokens in infos: {values}")

        return found[0]

    def root_bank_cache_from_cache(self, cache: Cache, index: int) -> typing.Optional[RootBankCache]:
        return cache.root_bank_cache[index]

    def load_root_bank(self, context: Context) -> RootBank:
        return RootBank.load(context, self.root_bank_address)

    def pick_node_bank(self, context: Context) -> NodeBank:
        root_bank: RootBank = self.load_root_bank(context)
        return root_bank.pick_node_bank(context)

    def __str__(self) -> str:
        return f"""« 𝚃𝚘𝚔𝚎𝚗𝙸𝚗𝚏𝚘 {self.token}
    Root Bank Address: {self.root_bank_address}
»"""

    def __repr__(self) -> str:
        return f"{self}"
