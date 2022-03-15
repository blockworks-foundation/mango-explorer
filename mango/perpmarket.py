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

from dataclasses import dataclass
from datetime import datetime, timedelta
from dateutil import parser
from decimal import Decimal
from solana.publickey import PublicKey

from .account import Account
from .accountinfo import AccountInfo
from .addressableaccount import AddressableAccount
from .combinableinstructions import CombinableInstructions
from .constants import SYSTEM_PROGRAM_ADDRESS
from .context import Context
from .datetimes import utc_now
from .group import Group
from .instructions import (
    build_mango_redeem_accrued_instructions,
    build_perp_cancel_all_orders_instructions,
    build_perp_cancel_order_instructions,
    build_perp_consume_events_instructions,
    build_perp_place_order_instructions,
)
from .layouts import layouts
from .loadedmarket import LoadedMarket
from .lotsizeconverter import LotSizeConverter, RaisingLotSizeConverter
from .markets import InventorySource, MarketType, Market
from .marketoperations import MarketInstructionBuilder, MarketOperations
from .metadata import Metadata
from .observables import Disposable
from .orders import Order, OrderBook, OrderType, Side
from .perpeventqueue import (
    PerpEvent,
    PerpEventQueue,
    PerpFillEvent,
    UnseenPerpEventChangesTracker,
)
from .perpmarketdetails import PerpMarketDetails
from .publickey import encode_public_key_for_sorting
from .tokens import Instrument, Token
from .tokenbank import TokenBank
from .wallet import Wallet
from .websocketsubscription import (
    IndividualWebSocketSubscriptionManager,
    WebSocketAccountSubscription,
    WebSocketSubscriptionManager,
)
from .version import Version


# # 🥭 FundingRate class
#
# A simple way to package details of a funding rate in a single object.
#
@dataclass
class FundingRate:
    symbol: str
    rate: Decimal
    oracle_price: Decimal
    open_interest: Decimal
    from_: datetime
    to: datetime

    @staticmethod
    def from_stats_data(
        symbol: str,
        lot_size_converter: LotSizeConverter,
        oldest_stats: typing.Dict[str, typing.Any],
        newest_stats: typing.Dict[str, typing.Any],
    ) -> "FundingRate":
        oldest_short_funding = Decimal(oldest_stats["shortFunding"])
        oldest_long_funding = Decimal(oldest_stats["longFunding"])
        oldest_oracle_price = Decimal(oldest_stats["baseOraclePrice"])
        from_timestamp = parser.parse(oldest_stats["time"]).replace(microsecond=0)

        newest_short_funding = Decimal(newest_stats["shortFunding"])
        newest_long_funding = Decimal(newest_stats["longFunding"])
        newest_oracle_price = Decimal(newest_stats["baseOraclePrice"])
        to_timestamp = parser.parse(newest_stats["time"]).replace(microsecond=0)
        raw_open_interest = Decimal(newest_stats["openInterest"])
        open_interest = (
            lot_size_converter.base_size_lots_to_number(raw_open_interest) / 2
        )

        average_oracle_price = (oldest_oracle_price + newest_oracle_price) / 2
        average_oracle_price = newest_oracle_price

        start_funding = (oldest_long_funding + oldest_short_funding) / 2
        end_funding = (newest_long_funding + newest_short_funding) / 2
        funding_difference = end_funding - start_funding

        funding_in_quote_decimals = lot_size_converter.quote.shift_to_decimals(
            funding_difference
        )

        base_price_in_base_lots = average_oracle_price * lot_size_converter.lot_size
        funding_rate = funding_in_quote_decimals / base_price_in_base_lots
        return FundingRate(
            symbol=symbol,
            rate=funding_rate,
            oracle_price=average_oracle_price,
            open_interest=open_interest,
            from_=from_timestamp,
            to=to_timestamp,
        )

    @property
    def extrapolated_apr(self) -> Decimal:
        # From Max (in Discord DM):
        # hpr * 24 * 365 = apr
        # ...
        # hpr * 8760 = apr
        return self.rate * Decimal(8760)

    @property
    def extrapolated_apy(self) -> Decimal:
        # From Max (in Discord DM):
        # (1 + hpr) ^ 8760 = apy + 1
        return ((Decimal(1) + self.rate) ** Decimal(8760)) - Decimal(1)

    def __str__(self) -> str:
        return f"""« FundingRate {self.symbol} {self.rate:,.8%}
    Period: {self.from_} to {self.to}
    Open Interest: {self.open_interest:,.8f}
    Extrapolated APR: {self.extrapolated_apr:,.8%}
    Extrapolated APY: {self.extrapolated_apy:,.8%}
»"""

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 PerpOrderBookSide class
#
# `PerpOrderBookSide` holds orders for one side of a market.
#
class PerpOrderBookSide(AddressableAccount):
    def __init__(
        self,
        account_info: AccountInfo,
        version: Version,
        meta_data: Metadata,
        perp_market_details: PerpMarketDetails,
        bump_index: Decimal,
        free_list_len: Decimal,
        free_list_head: Decimal,
        root_node: Decimal,
        leaf_count: Decimal,
        nodes: typing.Any,
    ) -> None:
        super().__init__(account_info)
        self.version: Version = version

        self.meta_data: Metadata = meta_data
        self.perp_market_details: PerpMarketDetails = perp_market_details
        self.bump_index: Decimal = bump_index
        self.free_list_len: Decimal = free_list_len
        self.free_list_head: Decimal = free_list_head
        self.root_node: Decimal = root_node
        self.leaf_count: Decimal = leaf_count
        self.nodes: typing.Any = nodes

    @staticmethod
    def from_layout(
        layout: typing.Any,
        account_info: AccountInfo,
        version: Version,
        perp_market_details: PerpMarketDetails,
    ) -> "PerpOrderBookSide":
        meta_data = Metadata.from_layout(layout.meta_data)
        bump_index: Decimal = layout.bump_index
        free_list_len: Decimal = layout.free_list_len
        free_list_head: Decimal = layout.free_list_head
        root_node: Decimal = layout.root_node
        leaf_count: Decimal = layout.leaf_count
        nodes: typing.Any = layout.nodes

        return PerpOrderBookSide(
            account_info,
            version,
            meta_data,
            perp_market_details,
            bump_index,
            free_list_len,
            free_list_head,
            root_node,
            leaf_count,
            nodes,
        )

    @staticmethod
    def parse(
        account_info: AccountInfo, perp_market_details: PerpMarketDetails
    ) -> "PerpOrderBookSide":
        data = account_info.data
        if len(data) != layouts.ORDERBOOK_SIDE.sizeof():
            raise Exception(
                f"PerpOrderBookSide data length ({len(data)}) does not match expected size ({layouts.ORDERBOOK_SIDE.sizeof()})"
            )

        layout = layouts.ORDERBOOK_SIDE.parse(data)
        return PerpOrderBookSide.from_layout(
            layout, account_info, Version.V1, perp_market_details
        )

    @staticmethod
    def load(
        context: Context, address: PublicKey, perp_market_details: PerpMarketDetails
    ) -> "PerpOrderBookSide":
        account_info = AccountInfo.load(context, address)
        if account_info is None:
            raise Exception(
                f"PerpOrderBookSide account not found at address '{address}'"
            )
        return PerpOrderBookSide.parse(account_info, perp_market_details)

    def subscribe(
        self,
        context: Context,
        websocketmanager: WebSocketSubscriptionManager,
        callback: typing.Callable[["PerpOrderBookSide"], None],
    ) -> Disposable:
        def __parser(account_info: AccountInfo) -> PerpOrderBookSide:
            return PerpOrderBookSide.parse(account_info, self.perp_market_details)

        subscription = WebSocketAccountSubscription(context, self.address, __parser)
        websocketmanager.add(subscription)
        subscription.publisher.subscribe(on_next=callback)  # type: ignore[call-arg]

        return subscription

    def orders(self) -> typing.Sequence[Order]:
        if self.leaf_count == 0:
            return []

        if self.meta_data.data_type == layouts.DATA_TYPE.Bids:
            order_side = Side.BUY
        else:
            order_side = Side.SELL

        stack = [self.root_node]
        orders: typing.List[Order] = []
        while len(stack) > 0:
            index = int(stack.pop())
            node = self.nodes[index]
            if node.type_name == "leaf":
                timestamp: datetime = node.timestamp
                expiration = Order.NoExpiration
                if node.time_in_force != 0:
                    expiration = timestamp + timedelta(
                        seconds=float(node.time_in_force)
                    )

                price = node.key["price"]
                quantity = node.quantity

                decimals_differential = (
                    self.perp_market_details.base_instrument.decimals
                    - self.perp_market_details.quote_token.token.decimals
                )
                native_to_ui = Decimal(10) ** decimals_differential
                quote_lot_size = self.perp_market_details.quote_lot_size
                base_lot_size = self.perp_market_details.base_lot_size
                actual_price = price * (quote_lot_size / base_lot_size) * native_to_ui

                base_factor = (
                    Decimal(10) ** self.perp_market_details.base_instrument.decimals
                )
                actual_quantity = (
                    quantity * self.perp_market_details.base_lot_size
                ) / base_factor

                orders += [
                    Order(
                        int(node.key["order_id"]),
                        node.client_order_id,
                        node.owner,
                        order_side,
                        actual_price,
                        actual_quantity,
                        OrderType.UNKNOWN,
                        timestamp=timestamp,
                        expiration=expiration,
                    )
                ]
            elif node.type_name == "inner":
                if order_side == Side.BUY:
                    stack = [*stack, node.children[0], node.children[1]]
                else:
                    stack = [*stack, node.children[1], node.children[0]]
        return orders

    def __str__(self) -> str:
        nodes = "\n        ".join(
            [str(node).replace("\n", "\n        ") for node in self.orders()]
        )
        return f"""« PerpOrderBookSide {self.version} [{self.address}]
    {self.meta_data}
    Perp Market: {self.perp_market_details}
    Bump Index: {self.bump_index}
    Free List: {self.free_list_head} (head) {self.free_list_len} (length)
    Root Node: {self.root_node}
    Leaf Count: {self.leaf_count}
        {nodes}
»"""


# # 🥭 PerpMarket class
#
# This class encapsulates our knowledge of a Mango perps market.
#
class PerpMarket(LoadedMarket):
    def __init__(
        self,
        mango_program_address: PublicKey,
        address: PublicKey,
        base: Instrument,
        quote: Token,
        underlying_perp_market: PerpMarketDetails,
    ) -> None:
        super().__init__(
            MarketType.PERP,
            mango_program_address,
            address,
            InventorySource.ACCOUNT,
            base,
            quote,
            RaisingLotSizeConverter(),
        )
        self.underlying_perp_market: PerpMarketDetails = underlying_perp_market
        self.lot_size_converter: LotSizeConverter = LotSizeConverter(
            base,
            underlying_perp_market.base_lot_size,
            quote,
            underlying_perp_market.quote_lot_size,
        )

    @staticmethod
    def isa(market: Market) -> bool:
        return market.type == MarketType.PERP

    @staticmethod
    def ensure(market: Market) -> "PerpMarket":
        if not PerpMarket.isa(market):
            raise Exception(
                f"Market for {market.fully_qualified_symbol} is not a Perp market"
            )
        return typing.cast(PerpMarket, market)

    @property
    def symbol(self) -> str:
        return f"{self.base.symbol}-PERP"

    @property
    def fully_qualified_symbol(self) -> str:
        return f"perp:{self.symbol}"

    @property
    def group(self) -> Group:
        return self.underlying_perp_market.group

    @property
    def bids_address(self) -> PublicKey:
        return self.underlying_perp_market.bids

    @property
    def asks_address(self) -> PublicKey:
        return self.underlying_perp_market.asks

    @property
    def event_queue_address(self) -> PublicKey:
        return self.underlying_perp_market.event_queue

    def parse_account_info_to_orders(
        self, account_info: AccountInfo
    ) -> typing.Sequence[Order]:
        side: PerpOrderBookSide = PerpOrderBookSide.parse(
            account_info, self.underlying_perp_market
        )
        return side.orders()

    def fetch_funding(self, context: Context) -> FundingRate:
        stats = context.fetch_stats(
            f"perp/funding_rate?mangoGroup={self.group.name}&market={self.symbol}"
        )
        newest_stats = stats[0]
        oldest_stats = stats[-1]

        return FundingRate.from_stats_data(
            self.symbol, self.lot_size_converter, oldest_stats, newest_stats
        )

    def unprocessed_events(self, context: Context) -> typing.Sequence[PerpEvent]:
        event_queue: PerpEventQueue = PerpEventQueue.load(
            context, self.event_queue_address, self.lot_size_converter
        )
        return event_queue.unprocessed_events

    def on_fill(
        self, context: Context, handler: typing.Callable[[PerpFillEvent], None]
    ) -> Disposable:
        def _fill_filter(item: PerpEvent) -> None:
            if isinstance(item, PerpFillEvent):
                handler(item)

        return self.on_event(context, _fill_filter)

    def on_event(
        self, context: Context, handler: typing.Callable[[PerpEvent], None]
    ) -> Disposable:
        disposer = Disposable()
        initial: PerpEventQueue = PerpEventQueue.load(
            context, self.event_queue_address, self.lot_size_converter
        )

        manager = IndividualWebSocketSubscriptionManager(context)
        disposer.add_disposable(manager)

        splitter: UnseenPerpEventChangesTracker = UnseenPerpEventChangesTracker(initial)

        def __split_handler(pev: PerpEventQueue) -> None:
            for event in splitter.unseen(pev):
                handler(event)

        subscription = initial.subscribe(context, manager, __split_handler)
        disposer.add_disposable(subscription)

        manager.open()

        return disposer

    def __str__(self) -> str:
        underlying: str = f"{self.underlying_perp_market}".replace("\n", "\n    ")
        return f"""« PerpMarket {self.symbol} {self.address} [{self.program_address}]
    {underlying}
»"""


# # 🥭 PerpMarketInstructionBuilder
#
# This file deals with building instructions for Perp markets.
#
# As a matter of policy for all InstructionBuidlers, construction and build_* methods should all work with
# existing data, requiring no fetches from Solana or other sources. All necessary data should all be loaded
# on initial setup in the `load()` method.
#
class PerpMarketInstructionBuilder(MarketInstructionBuilder):
    def __init__(
        self,
        context: Context,
        wallet: Wallet,
        perp_market: PerpMarket,
        group: Group,
        account: Account,
    ) -> None:
        super().__init__()
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.perp_market: PerpMarket = perp_market
        self.group: Group = group
        self.account: Account = account
        self.mngo_token_bank: TokenBank = self.group.liquidity_incentive_token_bank

    @staticmethod
    def load(
        context: Context,
        wallet: Wallet,
        perp_market: PerpMarket,
        group: Group,
        account: Account,
    ) -> "PerpMarketInstructionBuilder":
        return PerpMarketInstructionBuilder(
            context, wallet, perp_market, group, account
        )

    def build_cancel_order_instructions(
        self, order: Order, ok_if_missing: bool = False
    ) -> CombinableInstructions:
        return build_perp_cancel_order_instructions(
            self.context,
            self.wallet,
            self.account,
            self.perp_market.underlying_perp_market,
            order,
            ok_if_missing,
        )

    def build_place_order_instructions(self, order: Order) -> CombinableInstructions:
        return build_perp_place_order_instructions(
            self.context,
            self.wallet,
            self.perp_market.underlying_perp_market.group,
            self.account,
            self.perp_market.underlying_perp_market,
            order.price,
            order.quantity,
            order.client_id,
            order.side,
            order.order_type,
            order.reduce_only,
            expiration=order.expiration,
            match_limit=order.match_limit,
            reflink=self.context.reflink,
        )

    def build_settle_instructions(self) -> CombinableInstructions:
        return CombinableInstructions.empty()

    def build_crank_instructions(
        self, addresses: typing.Sequence[PublicKey], limit: Decimal = Decimal(32)
    ) -> CombinableInstructions:
        distinct_addresses: typing.List[PublicKey] = [self.account.address]
        for address in addresses:
            if address not in distinct_addresses:
                distinct_addresses += [address]

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

        return build_perp_consume_events_instructions(
            self.context,
            self.group,
            self.perp_market.underlying_perp_market,
            limited_addresses,
            limit,
        )

    def build_redeem_instructions(self) -> CombinableInstructions:
        return build_mango_redeem_accrued_instructions(
            self.context,
            self.wallet,
            self.perp_market,
            self.group,
            self.account,
            self.mngo_token_bank,
        )

    def build_cancel_all_orders_instructions(
        self, limit: Decimal = Decimal(32)
    ) -> CombinableInstructions:
        return build_perp_cancel_all_orders_instructions(
            self.context,
            self.wallet,
            self.account,
            self.perp_market.underlying_perp_market,
            limit,
        )

    def __str__(self) -> str:
        return """« PerpMarketInstructionBuilder »"""


# # 🥭 PerpMarketOperations
#
# This file deals with placing orders for Perps.
#
class PerpMarketOperations(MarketOperations):
    def __init__(
        self,
        context: Context,
        wallet: Wallet,
        account: Account,
        market_instruction_builder: PerpMarketInstructionBuilder,
    ) -> None:
        super().__init__(market_instruction_builder.perp_market)
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.market_instruction_builder: PerpMarketInstructionBuilder = (
            market_instruction_builder
        )
        self.account: Account = account

    @staticmethod
    def ensure(market_ops: MarketOperations) -> "PerpMarketOperations":
        if not isinstance(market_ops, PerpMarketOperations):
            raise Exception(
                f"MarketOperations for {market_ops.symbol} is not a PerpMarketOperations"
            )
        return market_ops

    @property
    def perp_market(self) -> PerpMarket:
        return self.market_instruction_builder.perp_market

    def cancel_order(
        self, order: Order, ok_if_missing: bool = False
    ) -> typing.Sequence[str]:
        self._logger.info(f"Cancelling {self.symbol} order {order}.")
        signers: CombinableInstructions = CombinableInstructions.from_wallet(
            self.wallet
        )
        cancel: CombinableInstructions = (
            self.market_instruction_builder.build_cancel_order_instructions(
                order, ok_if_missing=ok_if_missing
            )
        )
        crank = self._build_crank(add_self=True)
        settle = self.market_instruction_builder.build_settle_instructions()
        return (signers + cancel + crank + settle).execute(self.context)

    def place_order(
        self, order: Order, crank_limit: Decimal = Decimal(5)
    ) -> typing.Sequence[str]:
        client_id: int = order.client_id or self.context.generate_client_id()
        signers: CombinableInstructions = CombinableInstructions.from_wallet(
            self.wallet
        )
        order_with_client_id: Order = order.with_update(client_id=client_id)
        self._logger.info(f"Placing {self.symbol} order {order_with_client_id}.")
        place: CombinableInstructions = (
            self.market_instruction_builder.build_place_order_instructions(
                order_with_client_id
            )
        )
        crank = self._build_crank(add_self=True, limit=crank_limit)
        settle = self.market_instruction_builder.build_settle_instructions()
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
        crank = self._build_crank(limit=limit)
        return (signers + crank).execute(self.context)

    def create_openorders(self) -> PublicKey:
        return SYSTEM_PROGRAM_ADDRESS

    def ensure_openorders(self) -> PublicKey:
        return SYSTEM_PROGRAM_ADDRESS

    def load_orderbook(self) -> OrderBook:
        return self.perp_market.fetch_orderbook(self.context)

    def load_my_orders(
        self, cutoff: typing.Optional[datetime] = utc_now()
    ) -> typing.Sequence[Order]:
        orderbook: OrderBook = self.load_orderbook()
        return orderbook.all_orders_for_owner(self.account.address, cutoff)

    def _build_crank(
        self, limit: Decimal = Decimal(32), add_self: bool = False
    ) -> CombinableInstructions:
        accounts_to_crank: typing.List[PublicKey] = []
        for event_to_crank in self.perp_market.unprocessed_events(self.context):
            accounts_to_crank += event_to_crank.accounts_to_crank

        if add_self:
            accounts_to_crank += [self.account.address]

        if len(accounts_to_crank) == 0:
            return CombinableInstructions.empty()

        self._logger.debug(
            f"Building crank instruction with {len(accounts_to_crank)} public keys, throttled to {limit}"
        )
        return self.market_instruction_builder.build_crank_instructions(
            accounts_to_crank, limit
        )

    def __str__(self) -> str:
        return f"""« PerpMarketOperations [{self.symbol}] »"""


# # 🥭 PerpMarketStub class
#
# This class holds information to load a `PerpMarket` object but doesn't automatically load it.
#
class PerpMarketStub(Market):
    def __init__(
        self,
        mango_program_address: PublicKey,
        address: PublicKey,
        base: Instrument,
        quote: Token,
        group_address: PublicKey,
    ) -> None:
        super().__init__(
            MarketType.STUB,
            mango_program_address,
            address,
            InventorySource.ACCOUNT,
            base,
            quote,
            RaisingLotSizeConverter(),
        )
        self.group_address: PublicKey = group_address

    @property
    def fully_qualified_symbol(self) -> str:
        return f"perp:{self.symbol}"

    def load(
        self, context: Context, group: typing.Optional[Group] = None
    ) -> PerpMarket:
        actual_group: Group = group or Group.load(context, self.group_address)
        underlying_perp_market: PerpMarketDetails = PerpMarketDetails.load(
            context, self.address, actual_group
        )
        return PerpMarket(
            self.program_address,
            self.address,
            self.base,
            self.quote,
            underlying_perp_market,
        )

    @property
    def symbol(self) -> str:
        return f"{self.base.symbol}-PERP"

    def __str__(self) -> str:
        return (
            f"« PerpMarketStub {self.symbol} {self.address} [{self.program_address}] »"
        )
