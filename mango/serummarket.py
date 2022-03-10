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

from datetime import datetime
from decimal import Decimal
from pyserum.market.market import Market as PySerumMarket
from pyserum.market.orderbook import OrderBook as PySerumOrderBook
from solana.publickey import PublicKey

from mango.datetimes import utc_now

from .accountinfo import AccountInfo
from .combinableinstructions import CombinableInstructions
from .constants import SYSTEM_PROGRAM_ADDRESS
from .context import Context
from .instructions import (
    build_serum_consume_events_instructions,
    build_serum_create_openorders_instructions,
    build_serum_settle_instructions,
    build_serum_place_order_instructions,
)
from .loadedmarket import LoadedMarket
from .lotsizeconverter import LotSizeConverter, RaisingLotSizeConverter
from .markets import InventorySource, Market, MarketType
from .marketoperations import MarketInstructionBuilder, MarketOperations
from .openorders import OpenOrders
from .observables import Disposable
from .orders import Order, OrderBook, Side
from .publickey import encode_public_key_for_sorting
from .serumeventqueue import SerumEvent, SerumEventQueue, UnseenSerumEventChangesTracker
from .tokens import Instrument, Token
from .tokenaccount import TokenAccount
from .wallet import Wallet
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
            raise Exception(
                f"Market for {market.fully_qualified_symbol} is not a Serum market"
            )
        return typing.cast(SerumMarket, market)

    @property
    def fully_qualified_symbol(self) -> str:
        return f"serum:{self.symbol}"

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
            self.base,
            self.quote,
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


# # 🥭 SerumMarketInstructionBuilder
#
# This file deals with building instructions for Serum markets.
#
# As a matter of policy for all InstructionBuidlers, construction and build_* methods should all work with
# existing data, requiring no fetches from Solana or other sources. All necessary data should all be loaded
# on initial setup in the `load()` method.
#
class SerumMarketInstructionBuilder(MarketInstructionBuilder):
    def __init__(
        self,
        context: Context,
        wallet: Wallet,
        serum_market: SerumMarket,
        raw_market: PySerumMarket,
        base_token_account: TokenAccount,
        quote_token_account: TokenAccount,
        open_orders_address: typing.Optional[PublicKey],
        fee_discount_token_address: PublicKey,
    ) -> None:
        super().__init__()
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.serum_market: SerumMarket = serum_market
        self.raw_market: PySerumMarket = raw_market
        self.base_token_account: TokenAccount = base_token_account
        self.quote_token_account: TokenAccount = quote_token_account
        self.open_orders_address: typing.Optional[PublicKey] = open_orders_address
        self.fee_discount_token_address: PublicKey = fee_discount_token_address

    @staticmethod
    def load(
        context: Context, wallet: Wallet, serum_market: SerumMarket
    ) -> "SerumMarketInstructionBuilder":
        raw_market: PySerumMarket = PySerumMarket.load(
            context.client.compatible_client,
            serum_market.address,
            context.serum_program_address,
        )

        fee_discount_token_address: PublicKey = SYSTEM_PROGRAM_ADDRESS
        srm_instrument: typing.Optional[
            Instrument
        ] = context.instrument_lookup.find_by_symbol("SRM")
        if srm_instrument is not None:
            srm_token: Token = Token.ensure(srm_instrument)
            fee_discount_token_account = TokenAccount.fetch_largest_for_owner_and_token(
                context, wallet.address, srm_token
            )
            if fee_discount_token_account is not None:
                fee_discount_token_address = fee_discount_token_account.address

        open_orders_address: typing.Optional[PublicKey] = None
        all_open_orders = OpenOrders.load_for_market_and_owner(
            context,
            serum_market.address,
            wallet.address,
            context.serum_program_address,
            serum_market.base,
            serum_market.quote,
        )
        if len(all_open_orders) > 0:
            open_orders_address = all_open_orders[0].address

        base_token_account = TokenAccount.fetch_largest_for_owner_and_token(
            context, wallet.address, serum_market.base
        )
        if base_token_account is None:
            raise Exception(
                f"Could not find source token account for base token {serum_market.base.symbol}."
            )

        quote_token_account = TokenAccount.fetch_largest_for_owner_and_token(
            context, wallet.address, serum_market.quote
        )
        if quote_token_account is None:
            raise Exception(
                f"Could not find source token account for quote token {serum_market.quote.symbol}."
            )

        return SerumMarketInstructionBuilder(
            context,
            wallet,
            serum_market,
            raw_market,
            base_token_account,
            quote_token_account,
            open_orders_address,
            fee_discount_token_address,
        )

    def build_cancel_order_instructions(
        self, order: Order, ok_if_missing: bool = False
    ) -> CombinableInstructions:
        # For us to cancel an order, an open_orders account must already exist (or have existed).
        if self.open_orders_address is None:
            raise Exception(
                f"Cannot cancel order with client ID {order.client_id} - no OpenOrders account."
            )

        raw_instruction = self.raw_market.make_cancel_order_by_client_id_instruction(
            self.wallet.keypair, self.open_orders_address, order.client_id
        )
        return CombinableInstructions.from_instruction(raw_instruction)

    def build_place_order_instructions(self, order: Order) -> CombinableInstructions:
        if order.reduce_only:
            self._logger.warning(
                "Ignoring reduce_only - not supported on Serum markets"
            )

        if order.expiration != Order.NoExpiration:
            self._logger.warning("Ignoring expiration - not supported on Serum markets")

        if order.match_limit != Order.DefaultMatchLimit:
            self._logger.warning(
                "Ignoring match_limit - not supported on Serum markets"
            )

        ensure_open_orders = CombinableInstructions.empty()
        if self.open_orders_address is None:
            ensure_open_orders = self.build_create_openorders_instructions()

        if self.open_orders_address is None:
            raise Exception("Failed to find or create OpenOrders address")

        payer_token_account = (
            self.quote_token_account
            if order.side == Side.BUY
            else self.base_token_account
        )
        place = build_serum_place_order_instructions(
            self.context,
            self.wallet,
            self.raw_market,
            payer_token_account.address,
            self.open_orders_address,
            order.order_type,
            order.side,
            order.price,
            order.quantity,
            order.client_id,
            self.fee_discount_token_address,
        )

        return ensure_open_orders + place

    def build_settle_instructions(self) -> CombinableInstructions:
        if self.open_orders_address is None:
            return CombinableInstructions.empty()
        return build_serum_settle_instructions(
            self.context,
            self.wallet,
            self.raw_market,
            self.open_orders_address,
            self.base_token_account.address,
            self.quote_token_account.address,
        )

    def build_crank_instructions(
        self, addresses: typing.Sequence[PublicKey], limit: Decimal = Decimal(32)
    ) -> CombinableInstructions:
        if self.open_orders_address is None:
            self._logger.debug(
                "Returning empty crank instructions - no serum OpenOrders address provided."
            )
            return CombinableInstructions.empty()

        distinct_addresses: typing.List[PublicKey] = []
        for oo in addresses:
            if oo not in distinct_addresses:
                distinct_addresses += [oo]

        if len(distinct_addresses) > limit:
            self._logger.warn(
                f"Cranking limited to {limit} of {len(distinct_addresses)} addresses waiting to be cranked."
            )

        limited_addresses = distinct_addresses[
            0 : min(int(limit), len(distinct_addresses))
        ]
        limited_addresses.sort(key=encode_public_key_for_sorting)

        self._logger.debug(
            f"About to crank {len(limited_addresses)} addresses: {limited_addresses}"
        )
        return build_serum_consume_events_instructions(
            self.context,
            self.serum_market.address,
            self.raw_market.state.event_queue(),
            limited_addresses,
            int(limit),
        )

    def build_create_openorders_instructions(self) -> CombinableInstructions:
        create_open_orders = build_serum_create_openorders_instructions(
            self.context, self.wallet, self.raw_market
        )
        self.open_orders_address = create_open_orders.signers[0].public_key
        return create_open_orders

    def build_redeem_instructions(self) -> CombinableInstructions:
        return CombinableInstructions.empty()

    def __str__(self) -> str:
        return """« SerumMarketInstructionBuilder »"""


# # 🥭 SerumMarketOperations class
#
# This class performs standard operations on the Serum orderbook.
#
class SerumMarketOperations(MarketOperations):
    def __init__(
        self,
        context: Context,
        wallet: Wallet,
        market_instruction_builder: SerumMarketInstructionBuilder,
    ) -> None:
        super().__init__(market_instruction_builder.serum_market)
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.market_instruction_builder: SerumMarketInstructionBuilder = (
            market_instruction_builder
        )

    @staticmethod
    def ensure(market_ops: MarketOperations) -> "SerumMarketOperations":
        if not isinstance(market_ops, SerumMarketOperations):
            raise Exception(
                f"MarketOperations for {market_ops.symbol} is not a SerumMarketOperations"
            )
        return market_ops

    @property
    def serum_market(self) -> SerumMarket:
        return self.market_instruction_builder.serum_market

    def cancel_order(
        self, order: Order, ok_if_missing: bool = False
    ) -> typing.Sequence[str]:
        self._logger.info(
            f"Cancelling {self.serum_market.fully_qualified_symbol} order {order}."
        )
        signers: CombinableInstructions = CombinableInstructions.from_wallet(
            self.wallet
        )
        cancel: CombinableInstructions = (
            self.market_instruction_builder.build_cancel_order_instructions(
                order, ok_if_missing=ok_if_missing
            )
        )
        crank: CombinableInstructions = self._build_crank()
        settle: CombinableInstructions = (
            self.market_instruction_builder.build_settle_instructions()
        )
        return (signers + cancel + crank + settle).execute(self.context)

    def place_order(
        self, order: Order, crank_limit: Decimal = Decimal(5)
    ) -> typing.Sequence[str]:
        client_id: int = order.client_id or self.context.generate_client_id()
        signers: CombinableInstructions = CombinableInstructions.from_wallet(
            self.wallet
        )

        open_orders_address = (
            self.market_instruction_builder.open_orders_address
            or SYSTEM_PROGRAM_ADDRESS
        )
        order_with_client_id: Order = Order(
            id=0,
            client_id=client_id,
            side=order.side,
            price=order.price,
            quantity=order.quantity,
            owner=open_orders_address,
            order_type=order.order_type,
        )
        self._logger.info(
            f"Placing {self.serum_market.fully_qualified_symbol} order {order_with_client_id}."
        )
        place: CombinableInstructions = (
            self.market_instruction_builder.build_place_order_instructions(
                order_with_client_id
            )
        )

        crank: CombinableInstructions = self._build_crank(crank_limit)
        settle: CombinableInstructions = (
            self.market_instruction_builder.build_settle_instructions()
        )

        return (signers + place + crank + settle).execute(self.context)

    def settle(self) -> typing.Sequence[str]:
        signers: CombinableInstructions = CombinableInstructions.from_wallet(
            self.wallet
        )
        settle = self.market_instruction_builder.build_settle_instructions()
        return (signers + settle).execute(self.context)

    def crank(self, limit: Decimal = Decimal(32)) -> typing.Sequence[str]:
        signers: CombinableInstructions = CombinableInstructions.from_wallet(
            self.wallet
        )
        crank = self._build_crank(limit)
        return (signers + crank).execute(self.context)

    def create_openorders(self) -> PublicKey:
        signers: CombinableInstructions = CombinableInstructions.from_wallet(
            self.wallet
        )
        create_open_orders = (
            self.market_instruction_builder.build_create_openorders_instructions()
        )
        open_orders_address = create_open_orders.signers[0].public_key
        (signers + create_open_orders).execute(self.context)

        return open_orders_address

    def ensure_openorders(self) -> PublicKey:
        if self.market_instruction_builder.open_orders_address is not None:
            return self.market_instruction_builder.open_orders_address
        return self.create_openorders()

    def load_orderbook(self) -> OrderBook:
        return self.serum_market.fetch_orderbook(self.context)

    def load_my_orders(
        self, cutoff: typing.Optional[datetime] = utc_now()
    ) -> typing.Sequence[Order]:
        open_orders_address = self.market_instruction_builder.open_orders_address
        if not open_orders_address:
            return []

        orderbook: OrderBook = self.load_orderbook()
        return orderbook.all_orders_for_owner(open_orders_address, cutoff=cutoff)

    def _build_crank(
        self, limit: Decimal = Decimal(32), add_self: bool = False
    ) -> CombinableInstructions:
        open_orders_to_crank: typing.List[PublicKey] = []
        for event in self.serum_market.unprocessed_events(self.context):
            open_orders_to_crank += [event.public_key]
        self._logger.debug(f"open_orders_to_crank: {len(open_orders_to_crank)}")

        if add_self and self.market_instruction_builder.open_orders_address is not None:
            open_orders_to_crank += [
                self.market_instruction_builder.open_orders_address
            ]

        if len(open_orders_to_crank) == 0:
            return CombinableInstructions.empty()

        self._logger.debug(
            f"Building crank instruction with {len(open_orders_to_crank)} public keys, throttled to {limit}"
        )
        return self.market_instruction_builder.build_crank_instructions(
            open_orders_to_crank, limit
        )

    def __str__(self) -> str:
        return f"""« SerumMarketOperations [{self.serum_market.fully_qualified_symbol}] »"""


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

    @property
    def fully_qualified_symbol(self) -> str:
        return f"serum:{self.symbol}"

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
