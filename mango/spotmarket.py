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
import rx.operators
import typing

from datetime import datetime
from decimal import Decimal
from pyserum.market.market import Market as PySerumMarket
from pyserum.market.orderbook import OrderBook as PySerumOrderBook
from solana.publickey import PublicKey

from .account import Account
from .accountinfo import AccountInfo
from .combinableinstructions import CombinableInstructions
from .constants import SYSTEM_PROGRAM_ADDRESS
from .context import Context
from .datetimes import utc_now
from .group import GroupSlot, Group
from .instructions import (
    build_serum_consume_events_instructions,
    build_spot_cancel_order_instructions,
    build_spot_place_order_instructions,
    build_spot_settle_instructions,
    build_spot_create_openorders_instructions,
)
from .loadedmarket import LoadedMarket
from .lotsizeconverter import LotSizeConverter, RaisingLotSizeConverter
from .markets import InventorySource, MarketType, Market
from .marketoperations import MarketInstructionBuilder, MarketOperations
from .observables import Disposable
from .orders import Order, OrderBook
from .publickey import encode_public_key_for_sorting
from .serumeventqueue import SerumEvent, SerumEventQueue, UnseenSerumEventChangesTracker
from .tokens import Token
from .wallet import Wallet
from .websocketsubscription import (
    IndividualWebSocketSubscriptionManager,
    WebSocketAccountSubscription,
)


# # 🥭 SpotMarket class
#
# This class encapsulates our knowledge of a Serum spot market.
#
class SpotMarket(LoadedMarket):
    def __init__(
        self,
        serum_program_address: PublicKey,
        address: PublicKey,
        base: Token,
        quote: Token,
        group: Group,
        underlying_serum_market: PySerumMarket,
    ) -> None:
        super().__init__(
            MarketType.SPOT,
            serum_program_address,
            address,
            InventorySource.ACCOUNT,
            base,
            quote,
            RaisingLotSizeConverter(),
        )
        self.base: Token = base
        self.quote: Token = quote
        self.group: Group = group
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
        return market.type == MarketType.SPOT

    @staticmethod
    def ensure(market: Market) -> "SpotMarket":
        if not SpotMarket.isa(market):
            raise Exception(
                f"Market for {market.fully_qualified_symbol} is not a Spot market"
            )
        return typing.cast(SpotMarket, market)

    @property
    def fully_qualified_symbol(self) -> str:
        return f"spot:{self.symbol}"

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

    def derive_open_orders_address(
        self, context: Context, account: Account
    ) -> PublicKey:
        slot = account.slot_by_instrument(self.base)
        open_orders_address_and_nonce: typing.Tuple[
            PublicKey, int
        ] = PublicKey.find_program_address(
            [
                bytes(account.address),
                int(slot.index).to_bytes(8, "little"),
                b"OpenOrders",
            ],
            context.mango_program_address,
        )
        open_orders_address: PublicKey = open_orders_address_and_nonce[0]
        return open_orders_address

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
        return f"""« SpotMarket {self.symbol} {self.address} [{self.program_address}]
    Event Queue: {self.underlying_serum_market.state.event_queue()}
    Request Queue: {self.underlying_serum_market.state.request_queue()}
    Bids: {self.underlying_serum_market.state.bids()}
    Asks: {self.underlying_serum_market.state.asks()}
    Base: [lot size: {self.underlying_serum_market.state.base_lot_size()}] {self.underlying_serum_market.state.base_mint()}
    Quote: [lot size: {self.underlying_serum_market.state.quote_lot_size()}] {self.underlying_serum_market.state.quote_mint()}
»"""


# # 🥭 SpotMarketInstructionBuilder
#
# This file deals with building instructions for Spot markets.
#
# As a matter of policy for all InstructionBuidlers, construction and build_* methods should all work with
# existing data, requiring no fetches from Solana or other sources. All necessary data should all be loaded
# on initial setup in the `load()` method.
#
class SpotMarketInstructionBuilder(MarketInstructionBuilder):
    def __init__(
        self,
        context: Context,
        wallet: Wallet,
        spot_market: SpotMarket,
        group: Group,
        account: Account,
        raw_market: PySerumMarket,
        market_index: int,
        fee_discount_token_address: PublicKey,
    ) -> None:
        super().__init__()
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.spot_market: SpotMarket = spot_market
        self.group: Group = group
        self.account: Account = account
        self.raw_market: PySerumMarket = raw_market
        self.market_index: int = market_index
        self.fee_discount_token_address: PublicKey = fee_discount_token_address

        self.open_orders_address: typing.Optional[
            PublicKey
        ] = self.account.spot_open_orders_by_index[self.market_index]

    @staticmethod
    def load(
        context: Context,
        wallet: Wallet,
        spot_market: SpotMarket,
        group: Group,
        account: Account,
    ) -> "SpotMarketInstructionBuilder":
        raw_market: PySerumMarket = PySerumMarket.load(
            context.client.compatible_client,
            spot_market.address,
            context.serum_program_address,
        )

        msrm_balance = context.client.get_token_account_balance(group.msrm_vault)
        fee_discount_token_address: PublicKey
        if msrm_balance > 0:
            fee_discount_token_address = group.msrm_vault
            logging.debug(
                f"MSRM balance is: {msrm_balance} - using MSRM fee discount address {fee_discount_token_address}"
            )
        else:
            fee_discount_token_address = group.srm_vault
            logging.debug(
                f"MSRM balance is: {msrm_balance} - using SRM fee discount address {fee_discount_token_address}"
            )

        slot = group.slot_by_spot_market_address(spot_market.address)
        market_index = slot.index

        return SpotMarketInstructionBuilder(
            context,
            wallet,
            spot_market,
            group,
            account,
            raw_market,
            market_index,
            fee_discount_token_address,
        )

    def build_cancel_order_instructions(
        self, order: Order, ok_if_missing: bool = False
    ) -> CombinableInstructions:
        if self.open_orders_address is None:
            return CombinableInstructions.empty()

        return build_spot_cancel_order_instructions(
            self.context,
            self.wallet,
            self.group,
            self.account,
            self.raw_market,
            order,
            self.open_orders_address,
        )

    def build_place_order_instructions(self, order: Order) -> CombinableInstructions:
        if order.reduce_only:
            self._logger.warning("Ignoring reduce_only - not supported on Spot markets")

        if order.expiration != Order.NoExpiration:
            self._logger.warning("Ignoring expiration - not supported on Spot markets")

        if order.match_limit != Order.DefaultMatchLimit:
            self._logger.warning("Ignoring match_limit - not supported on Spot markets")

        slot = self.group.slot_by_spot_market_address(self.spot_market.address)
        market_index = slot.index
        open_orders_address: typing.Optional[
            PublicKey
        ] = self.account.spot_open_orders_by_index[market_index]

        instructions = CombinableInstructions.empty()
        if open_orders_address is None:
            # Spot OpenOrders accounts use a PDA as of v3.3
            open_orders_address = self.spot_market.derive_open_orders_address(
                self.context, self.account
            )
            instructions += build_spot_create_openorders_instructions(
                self.context,
                self.wallet,
                self.group,
                self.account,
                self.spot_market,
                open_orders_address,
            )

            # This line is a little nasty. Now that we know we have an OpenOrders account at
            # this address, update the IAccount so that future uses (like later in this
            # method) have access to it in the right place.
            #
            # This might cause problems if this instruction is never sent or the transaction
            # fails though.
            self.account.update_spot_open_orders_for_market(
                market_index, open_orders_address
            )

        instructions += build_spot_place_order_instructions(
            self.context,
            self.wallet,
            self.group,
            self.account,
            self.spot_market,
            open_orders_address,
            order.order_type,
            order.side,
            order.price,
            order.quantity,
            order.client_id,
            self.fee_discount_token_address,
        )

        return instructions

    def build_settle_instructions(self) -> CombinableInstructions:
        if self.open_orders_address is None:
            return CombinableInstructions.empty()

        base_slot: GroupSlot = self.group.slot_by_instrument(self.spot_market.base)
        if base_slot.base_token_bank is None:
            raise Exception(
                f"No token info for base instrument {self.spot_market.base.symbol} in group {self.group.address}"
            )
        base_rootbank = base_slot.base_token_bank.ensure_root_bank(self.context)
        base_nodebank = base_rootbank.pick_node_bank(self.context)

        quote_rootbank = self.group.shared_quote.ensure_root_bank(self.context)
        quote_nodebank = quote_rootbank.pick_node_bank(self.context)
        return build_spot_settle_instructions(
            self.context,
            self.wallet,
            self.account,
            self.raw_market,
            self.group,
            self.open_orders_address,
            base_rootbank,
            base_nodebank,
            quote_rootbank,
            quote_nodebank,
        )

    def build_crank_instructions(
        self, addresses: typing.Sequence[PublicKey], limit: Decimal = Decimal(32)
    ) -> CombinableInstructions:
        if self.open_orders_address is None:
            self._logger.debug(
                "Returning empty crank instructions - no spot OpenOrders address provided."
            )
            return CombinableInstructions.empty()

        distinct_addresses: typing.List[PublicKey] = [self.open_orders_address]
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
            self.spot_market.address,
            self.raw_market.state.event_queue(),
            limited_addresses,
            int(limit),
        )

    def build_redeem_instructions(self) -> CombinableInstructions:
        return CombinableInstructions.empty()

    def build_create_openorders_instructions(self) -> CombinableInstructions:
        # Spot OpenOrders accounts use a PDA as of v3.3
        open_orders_address: PublicKey = self.spot_market.derive_open_orders_address(
            self.context, self.account
        )
        return build_spot_create_openorders_instructions(
            self.context,
            self.wallet,
            self.group,
            self.account,
            self.spot_market,
            open_orders_address,
        )

    def __str__(self) -> str:
        return f"« SpotMarketInstructionBuilder [{self.spot_market.fully_qualified_symbol}] »"


# # 🥭 SpotMarketOperations class
#
# This class puts trades on the Serum orderbook. It doesn't do anything complicated.
#
class SpotMarketOperations(MarketOperations):
    def __init__(
        self,
        context: Context,
        wallet: Wallet,
        account: Account,
        market_instruction_builder: SpotMarketInstructionBuilder,
    ) -> None:
        super().__init__(market_instruction_builder.spot_market)
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.account: Account = account
        self.market_instruction_builder: SpotMarketInstructionBuilder = (
            market_instruction_builder
        )

        self.market_index: int = self.group.slot_by_spot_market_address(
            self.spot_market.address
        ).index
        self.open_orders_address: typing.Optional[
            PublicKey
        ] = self.account.spot_open_orders_by_index[self.market_index]

    @staticmethod
    def ensure(market_ops: MarketOperations) -> "SpotMarketOperations":
        if not isinstance(market_ops, SpotMarketOperations):
            raise Exception(
                f"MarketOperations for {market_ops.symbol} is not a SpotMarketOperations"
            )
        return market_ops

    @property
    def spot_market(self) -> SpotMarket:
        return self.market_instruction_builder.spot_market

    @property
    def group(self) -> Group:
        return self.market_instruction_builder.group

    def cancel_order(
        self, order: Order, ok_if_missing: bool = False
    ) -> typing.Sequence[str]:
        self._logger.info(
            f"Cancelling {self.spot_market.fully_qualified_symbol} order {order}."
        )
        signers: CombinableInstructions = CombinableInstructions.from_wallet(
            self.wallet
        )
        cancel: CombinableInstructions = (
            self.market_instruction_builder.build_cancel_order_instructions(
                order, ok_if_missing=ok_if_missing
            )
        )
        crank: CombinableInstructions = self._build_crank(add_self=True)
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

        order_with_client_id: Order = order.with_update(
            client_id=client_id
        ).with_update(owner=self.open_orders_address or SYSTEM_PROGRAM_ADDRESS)
        self._logger.info(
            f"Placing {self.spot_market.fully_qualified_symbol} order {order}."
        )
        place: CombinableInstructions = (
            self.market_instruction_builder.build_place_order_instructions(
                order_with_client_id
            )
        )
        crank: CombinableInstructions = self._build_crank(
            limit=crank_limit, add_self=True
        )
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
        crank = self._build_crank(limit, add_self=False)
        return (signers + crank).execute(self.context)

    def create_openorders(self) -> PublicKey:
        signers: CombinableInstructions = CombinableInstructions.from_wallet(
            self.wallet
        )
        create_open_orders: CombinableInstructions = (
            self.market_instruction_builder.build_create_openorders_instructions()
        )
        (signers + create_open_orders).execute(self.context)

        # These lines are a little nasty. Now that we know we have an OpenOrders account at this address,
        # update the Account so that future uses (like later in this method) have access to it in the right
        # place.
        open_orders_address: PublicKey = self.spot_market.derive_open_orders_address(
            self.context, self.account
        )
        self.account.update_spot_open_orders_for_market(
            self.market_index, open_orders_address
        )

        return open_orders_address

    def ensure_openorders(self) -> PublicKey:
        existing: typing.Optional[PublicKey] = self.account.spot_open_orders_by_index[
            self.market_index
        ]
        if existing is not None:
            return existing
        return self.create_openorders()

    def load_orderbook(self) -> OrderBook:
        return self.spot_market.fetch_orderbook(self.context)

    def load_my_orders(
        self, cutoff: typing.Optional[datetime] = utc_now()
    ) -> typing.Sequence[Order]:
        if not self.open_orders_address:
            return []

        orderbook: OrderBook = self.load_orderbook()
        return orderbook.all_orders_for_owner(self.open_orders_address, cutoff=cutoff)

    def _build_crank(
        self, limit: Decimal = Decimal(32), add_self: bool = False
    ) -> CombinableInstructions:
        open_orders_to_crank: typing.List[PublicKey] = []
        for event in self.spot_market.unprocessed_events(self.context):
            open_orders_to_crank += [event.public_key]

        if add_self and self.open_orders_address is not None:
            open_orders_to_crank += [self.open_orders_address]

        if len(open_orders_to_crank) == 0:
            return CombinableInstructions.empty()

        self._logger.debug(
            f"Building crank instruction with {len(open_orders_to_crank)} public keys, throttled to {limit}"
        )
        return self.market_instruction_builder.build_crank_instructions(
            open_orders_to_crank, limit
        )

    def __str__(self) -> str:
        return f"« SpotMarketOperations [{self.spot_market.fully_qualified_symbol}] »"


# # 🥭 SpotMarketStub class
#
# This class holds information to load a `SpotMarket` object but doesn't automatically load it.
#
class SpotMarketStub(Market):
    def __init__(
        self,
        serum_program_address: PublicKey,
        address: PublicKey,
        base: Token,
        quote: Token,
        group_address: PublicKey,
    ) -> None:
        super().__init__(
            MarketType.STUB,
            serum_program_address,
            address,
            InventorySource.ACCOUNT,
            base,
            quote,
            RaisingLotSizeConverter(),
        )
        self.base: Token = base
        self.quote: Token = quote
        self.group_address: PublicKey = group_address

    @property
    def fully_qualified_symbol(self) -> str:
        return f"spot:{self.symbol}"

    def load(self, context: Context, group: typing.Optional[Group]) -> SpotMarket:
        actual_group: Group = group or Group.load(context, self.group_address)
        underlying_serum_market: PySerumMarket = PySerumMarket.load(
            context.client.compatible_client,
            self.address,
            context.serum_program_address,
        )
        return SpotMarket(
            self.program_address,
            self.address,
            self.base,
            self.quote,
            actual_group,
            underlying_serum_market,
        )

    def __str__(self) -> str:
        return (
            f"« SpotMarketStub {self.symbol} {self.address} [{self.program_address}] »"
        )
