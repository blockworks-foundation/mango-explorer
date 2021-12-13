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

import typing

from decimal import Decimal
from pyserum.market.market import Market as PySerumMarket
from pyserum.market.orderbook import OrderBook as PySerumOrderBook
from solana.publickey import PublicKey

from .accountinfo import AccountInfo
from .context import Context
from .group import Group
from .loadedmarket import LoadedMarket
from .lotsizeconverter import LotSizeConverter, RaisingLotSizeConverter
from .market import Market, InventorySource
from .orders import Order
from .serumeventqueue import SerumEvent, SerumEventQueue
from .token import Token


# # 🥭 SpotMarket class
#
# This class encapsulates our knowledge of a Serum spot market.
#
class SpotMarket(LoadedMarket):
    def __init__(self, serum_program_address: PublicKey, address: PublicKey, base: Token, quote: Token,
                 group: Group, underlying_serum_market: PySerumMarket) -> None:
        super().__init__(serum_program_address, address, InventorySource.ACCOUNT, base, quote, RaisingLotSizeConverter())
        self.base: Token = base
        self.quote: Token = quote
        self.group: Group = group
        self.underlying_serum_market: PySerumMarket = underlying_serum_market
        base_lot_size: Decimal = Decimal(underlying_serum_market.state.base_lot_size())
        quote_lot_size: Decimal = Decimal(underlying_serum_market.state.quote_lot_size())
        self.lot_size_converter: LotSizeConverter = LotSizeConverter(base, base_lot_size, quote, quote_lot_size)

    @property
    def bids_address(self) -> PublicKey:
        return self.underlying_serum_market.state.bids()

    @property
    def asks_address(self) -> PublicKey:
        return self.underlying_serum_market.state.asks()

    def parse_account_info_to_orders(self, account_info: AccountInfo) -> typing.Sequence[Order]:
        orderbook: PySerumOrderBook = PySerumOrderBook.from_bytes(self.underlying_serum_market.state, account_info.data)
        return list(map(Order.from_serum_order, orderbook.orders()))

    def unprocessed_events(self, context: Context) -> typing.Sequence[SerumEvent]:
        event_queue: SerumEventQueue = SerumEventQueue.load(context, self.underlying_serum_market.state.event_queue())
        return event_queue.unprocessed_events

    def __str__(self) -> str:
        return f"""« SpotMarket {self.symbol} {self.address} [{self.program_address}]
    Event Queue: {self.underlying_serum_market.state.event_queue()}
    Request Queue: {self.underlying_serum_market.state.request_queue()}
    Bids: {self.underlying_serum_market.state.bids()}
    Asks: {self.underlying_serum_market.state.asks()}
    Base: [lot size: {self.underlying_serum_market.state.base_lot_size()}] {self.underlying_serum_market.state.base_mint()}
    Quote: [lot size: {self.underlying_serum_market.state.quote_lot_size()}] {self.underlying_serum_market.state.quote_mint()}
»"""


# # 🥭 SpotMarketStub class
#
# This class holds information to load a `SpotMarket` object but doesn't automatically load it.
#
class SpotMarketStub(Market):
    def __init__(self, serum_program_address: PublicKey, address: PublicKey, base: Token, quote: Token,
                 group_address: PublicKey) -> None:
        super().__init__(serum_program_address, address, InventorySource.ACCOUNT, base, quote, RaisingLotSizeConverter())
        self.base: Token = base
        self.quote: Token = quote
        self.group_address: PublicKey = group_address

    def load(self, context: Context, group: typing.Optional[Group]) -> SpotMarket:
        actual_group: Group = group or Group.load(context, self.group_address)
        underlying_serum_market: PySerumMarket = PySerumMarket.load(
            context.client.compatible_client, self.address, context.serum_program_address)
        return SpotMarket(self.program_address, self.address, self.base, self.quote, actual_group, underlying_serum_market)

    def __str__(self) -> str:
        return f"« SpotMarketStub {self.symbol} {self.address} [{self.program_address}] »"
