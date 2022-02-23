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

import rx.operators
import typing

from decimal import Decimal
from pyserum.market.market import Market as PySerumMarket
from pyserum.market.orderbook import OrderBook as PySerumOrderBook
from solana.publickey import PublicKey

from .accountinfo import AccountInfo
from .context import Context
from .loadedmarket import LoadedMarket
from .lotsizeconverter import LotSizeConverter, RaisingLotSizeConverter
from .market import InventorySource, Market, MarketType
from .openorders import OpenOrders
from .observables import Disposable
from .orders import Order
from .serumeventqueue import SerumEvent, SerumEventQueue, UnseenSerumEventChangesTracker
from .token import Token
from .websocketsubscription import (
    IndividualWebSocketSubscriptionManager,
    WebSocketAccountSubscription,
)


# # 🥭 SerumMarket class
#
# This class encapsulates our knowledge of a Serum spot market.
#
class SerumMarket(LoadedMarket):
    def __init__(
        self,
        serum_program_address: PublicKey,
        address: PublicKey,
        base: Token,
        quote: Token,
        underlying_serum_market: PySerumMarket,
    ) -> None:
        super().__init__(
            MarketType.SERUM,
            serum_program_address,
            address,
            InventorySource.SPL_TOKENS,
            base,
            quote,
            RaisingLotSizeConverter(),
        )
        self.base: Token = base
        self.quote: Token = quote
        self.underlying_serum_market: PySerumMarket = underlying_serum_market
        base_lot_size: Decimal = Decimal(underlying_serum_market.state.base_lot_size())
        quote_lot_size: Decimal = Decimal(
            underlying_serum_market.state.quote_lot_size()
        )
        self.lot_size_converter: LotSizeConverter = LotSizeConverter(
            base, base_lot_size, quote, quote_lot_size
        )

    @staticmethod
    def isa(market: Market) -> bool:
        return market.type == MarketType.SERUM

    @staticmethod
    def ensure(market: Market) -> "SerumMarket":
        if not SerumMarket.isa(market):
            raise Exception(f"Market for {market.symbol} is not a Serum market")
        return typing.cast(SerumMarket, market)

    @property
    def bids_address(self) -> PublicKey:
        return self.underlying_serum_market.state.bids()

    @property
    def asks_address(self) -> PublicKey:
        return self.underlying_serum_market.state.asks()

    @property
    def event_queue_address(self) -> PublicKey:
        return self.underlying_serum_market.state.event_queue()

    def parse_account_info_to_orders(
        self, account_info: AccountInfo
    ) -> typing.Sequence[Order]:
        orderbook: PySerumOrderBook = PySerumOrderBook.from_bytes(
            self.underlying_serum_market.state, account_info.data
        )
        return list(map(Order.from_serum_order, orderbook.orders()))

    def unprocessed_events(self, context: Context) -> typing.Sequence[SerumEvent]:
        event_queue: SerumEventQueue = SerumEventQueue.load(
            context, self.event_queue_address
        )
        return event_queue.unprocessed_events

    def find_openorders_address_for_owner(
        self, context: Context, owner: PublicKey
    ) -> typing.Optional[PublicKey]:
        all_open_orders = OpenOrders.load_for_market_and_owner(
            context,
            self.address,
            owner,
            context.serum_program_address,
            self.base.decimals,
            self.quote.decimals,
        )
        if len(all_open_orders) == 0:
            return None
        return all_open_orders[0].address

    def on_fill(
        self, context: Context, handler: typing.Callable[[SerumEvent], None]
    ) -> Disposable:
        def _fill_filter(item: SerumEvent) -> None:
            if item.event_flags.fill:
                handler(item)

        return self.on_event(context, _fill_filter)

    def on_event(
        self, context: Context, handler: typing.Callable[[SerumEvent], None]
    ) -> Disposable:
        disposer = Disposable()
        event_queue_address = self.event_queue_address
        initial: SerumEventQueue = SerumEventQueue.load(
            context, self.event_queue_address
        )

        splitter: UnseenSerumEventChangesTracker = UnseenSerumEventChangesTracker(
            initial
        )
        event_queue_subscription = WebSocketAccountSubscription(
            context, event_queue_address, SerumEventQueue.parse
        )
        disposer.add_disposable(event_queue_subscription)

        manager = IndividualWebSocketSubscriptionManager(context)
        disposer.add_disposable(manager)
        manager.add(event_queue_subscription)

        publisher = event_queue_subscription.publisher.pipe(
            rx.operators.flat_map(splitter.unseen)
        )

        individual_event_subscription = publisher.subscribe(on_next=handler)
        disposer.add_disposable(individual_event_subscription)

        manager.open()

        return disposer

    def __str__(self) -> str:
        return f"""« SerumMarket {self.symbol} {self.address} [{self.program_address}]
    Event Queue: {self.underlying_serum_market.state.event_queue()}
    Request Queue: {self.underlying_serum_market.state.request_queue()}
    Bids: {self.underlying_serum_market.state.bids()}
    Asks: {self.underlying_serum_market.state.asks()}
    Base: [lot size: {self.underlying_serum_market.state.base_lot_size()}] {self.underlying_serum_market.state.base_mint()}
    Quote: [lot size: {self.underlying_serum_market.state.quote_lot_size()}] {self.underlying_serum_market.state.quote_mint()}
»"""


# # 🥭 SerumMarketStub class
#
# This class holds information to load a `SerumMarket` object but doesn't automatically load it.
#
class SerumMarketStub(Market):
    def __init__(
        self,
        serum_program_address: PublicKey,
        address: PublicKey,
        base: Token,
        quote: Token,
    ) -> None:
        super().__init__(
            MarketType.STUB,
            serum_program_address,
            address,
            InventorySource.SPL_TOKENS,
            base,
            quote,
            RaisingLotSizeConverter(),
        )
        self.base: Token = base
        self.quote: Token = quote

    def load(self, context: Context) -> SerumMarket:
        underlying_serum_market: PySerumMarket = PySerumMarket.load(
            context.client.compatible_client,
            self.address,
            context.serum_program_address,
        )
        return SerumMarket(
            self.program_address,
            self.address,
            self.base,
            self.quote,
            underlying_serum_market,
        )

    def __str__(self) -> str:
        return (
            f"« SerumMarketStub {self.symbol} {self.address} [{self.program_address}] »"
        )
