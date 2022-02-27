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
import rx.operators
import typing

from solana.publickey import PublicKey

from .accountinfo import AccountInfo
from .context import Context
from .lotsizeconverter import LotSizeConverter
from .markets import InventorySource, MarketType, Market
from .observables import Disposable
from .orders import Order, OrderBook
from .tokens import Instrument, Token
from .websocketsubscription import (
    SharedWebSocketSubscriptionManager,
    WebSocketAccountSubscription,
)


class Event(typing.Protocol):
    @property
    def accounts_to_crank(self) -> typing.Sequence[PublicKey]:
        raise NotImplementedError(
            "Event.accounts_to_crank is not implemented on the Protocol."
        )


class FillEvent(Event, typing.Protocol):
    pass


# # 🥭 LoadedMarket class
#
# This class describes a crypto market. It *must* have an address, a base token and a quote token.
#
class LoadedMarket(Market):
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
        super().__init__(
            type,
            program_address,
            address,
            inventory_source,
            base,
            quote,
            lot_size_converter,
        )

    @property
    @abc.abstractproperty
    def bids_address(self) -> PublicKey:
        raise NotImplementedError(
            "LoadedMarket.bids_address() is not implemented on the base type."
        )

    @property
    @abc.abstractproperty
    def asks_address(self) -> PublicKey:
        raise NotImplementedError(
            "LoadedMarket.asks_address() is not implemented on the base type."
        )

    @property
    @abc.abstractproperty
    def event_queue_address(self) -> PublicKey:
        raise NotImplementedError(
            "LoadedMarket.event_queue_address() is not implemented on the base type."
        )

    @abc.abstractmethod
    def on_fill(
        self, context: Context, handler: typing.Callable[[FillEvent], None]
    ) -> Disposable:
        raise NotImplementedError(
            "LoadedMarket.on_fill() is not implemented on the base type."
        )

    @abc.abstractmethod
    def on_event(
        self, context: Context, handler: typing.Callable[[Event], None]
    ) -> Disposable:
        raise NotImplementedError(
            "LoadedMarket.on_event() is not implemented on the base type."
        )

    def on_orderbook_change(
        self, context: Context, handler: typing.Callable[[OrderBook], None]
    ) -> Disposable:
        disposer = Disposable()

        [bids_info, asks_info] = AccountInfo.load_multiple(
            context, [self.bids_address, self.asks_address]
        )

        stored: OrderBook = self.parse_account_infos_to_orderbook(bids_info, asks_info)

        def _update_bids(account_info: AccountInfo) -> OrderBook:
            new_bids = self.parse_account_info_to_orders(account_info)
            stored.bids = new_bids
            return OrderBook(
                self.symbol, self.lot_size_converter, new_bids, stored.asks
            )

        def _update_asks(account_info: AccountInfo) -> OrderBook:
            new_asks = self.parse_account_info_to_orders(account_info)
            stored.asks = new_asks
            return OrderBook(
                self.symbol, self.lot_size_converter, stored.bids, new_asks
            )

        websocket = SharedWebSocketSubscriptionManager(context)
        disposer.add_disposable(websocket)

        bids_subscription = WebSocketAccountSubscription[OrderBook](
            context, self.bids_address, _update_bids
        )
        websocket.add(bids_subscription)

        asks_subscription = WebSocketAccountSubscription[OrderBook](
            context, self.asks_address, _update_asks
        )
        websocket.add(asks_subscription)

        orderbook_changes = bids_subscription.publisher.pipe(
            rx.operators.merge(asks_subscription.publisher)
        )

        individual_event_subscription = orderbook_changes.subscribe(on_next=handler)
        disposer.add_disposable(individual_event_subscription)

        websocket.open()

        return disposer

    @abc.abstractmethod
    def parse_account_info_to_orders(
        self, account_info: AccountInfo
    ) -> typing.Sequence[Order]:
        raise NotImplementedError(
            "LoadedMarket.parse_account_info_to_orders() is not implemented on the base type."
        )

    def parse_account_infos_to_orderbook(
        self, bids_account_info: AccountInfo, asks_account_info: AccountInfo
    ) -> OrderBook:
        bids_orderbook = self.parse_account_info_to_orders(bids_account_info)
        asks_orderbook = self.parse_account_info_to_orders(asks_account_info)
        return OrderBook(
            self.symbol, self.lot_size_converter, bids_orderbook, asks_orderbook
        )

    def fetch_orderbook(self, context: Context) -> OrderBook:
        [bids_info, asks_info] = AccountInfo.load_multiple(
            context, [self.bids_address, self.asks_address]
        )
        return self.parse_account_infos_to_orderbook(bids_info, asks_info)
