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

from decimal import Decimal
from solana.publickey import PublicKey

from .constants import SYSTEM_PROGRAM_ADDRESS
from .lotsizeconverter import LotSizeConverter, NullLotSizeConverter
from .token import Token


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
    def __init__(self, program_address: PublicKey, address: PublicKey, inventory_source: InventorySource, base: Token, quote: Token, lot_size_converter: LotSizeConverter):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.program_address: PublicKey = program_address
        self.address: PublicKey = address
        self.inventory_source: InventorySource = inventory_source
        self.base: Token = base
        self.quote: Token = quote
        self.lot_size_converter: LotSizeConverter = lot_size_converter

    @property
    def symbol(self) -> str:
        return f"{self.base.symbol}/{self.quote.symbol}"

    def __str__(self) -> str:
        return f"« 𝙼𝚊𝚛𝚔𝚎𝚝 {self.symbol} »"

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 DryRunMarket class
#
# A fake `Market` that can be safely used in dry runs.
#
class DryRunMarket(Market):
    def __init__(self, market_name: str):
        program_address: PublicKey = SYSTEM_PROGRAM_ADDRESS
        address: PublicKey = SYSTEM_PROGRAM_ADDRESS
        inventory_source: InventorySource = InventorySource.SPL_TOKENS
        base: Token = Token("DRYRUNBASE", "DryRunBase", SYSTEM_PROGRAM_ADDRESS, Decimal(6))
        quote: Token = Token("DRYRUNQUOTE", "DryRunQuote", SYSTEM_PROGRAM_ADDRESS, Decimal(6))
        lot_size_converter: LotSizeConverter = NullLotSizeConverter()
        super().__init__(program_address, address, inventory_source, base, quote, lot_size_converter)
        self.market_name: str = market_name

    @property
    def symbol(self) -> str:
        return self.market_name
