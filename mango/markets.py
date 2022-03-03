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


import abc
import enum
import logging

from solana.publickey import PublicKey

from .lotsizeconverter import LotSizeConverter
from .tokens import Instrument, Token


class MarketType(enum.Enum):
    STUB = enum.auto()
    SERUM = enum.auto()
    SPOT = enum.auto()
    PERP = enum.auto()

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self}"


class InventorySource(enum.Enum):
    SPL_TOKENS = enum.auto()
    ACCOUNT = enum.auto()

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 Market class
#
# This class describes a crypto market. It *must* have an address, a base token and a quote token.
#
class Market(metaclass=abc.ABCMeta):
    def __init__(
        self,
        type: MarketType,
        program_address: PublicKey,
        address: PublicKey,
        inventory_source: InventorySource,
        base: Instrument,
        quote: Token,
        lot_size_converter: LotSizeConverter,
    ) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.type: MarketType = type
        self.program_address: PublicKey = program_address
        self.address: PublicKey = address
        self.inventory_source: InventorySource = inventory_source
        self.base: Instrument = base
        self.quote: Token = quote
        self.lot_size_converter: LotSizeConverter = lot_size_converter

    @staticmethod
    def symbols_match(symbol1: str, symbol2: str) -> bool:
        return symbol1.upper() == symbol2.upper()

    def symbol_matches(self, symbol: str) -> bool:
        return self.symbol.upper() == symbol.upper()

    @property
    def symbol(self) -> str:
        return f"{self.base.symbol}/{self.quote.symbol}"

    @property
    @abc.abstractproperty
    def fully_qualified_symbol(self) -> str:
        raise NotImplementedError(
            "Market.fully_qualified_symbol is not implemented on the base type."
        )

    def __str__(self) -> str:
        return f"« Market {self.symbol} »"

    def __repr__(self) -> str:
        return f"{self}"
