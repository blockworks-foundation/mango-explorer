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

import rx
import rx.disposable
import rx.subject
import rx.operators as ops
import typing

from datetime import datetime
from dateutil import parser
from decimal import Decimal
from solana.publickey import PublicKey

from .accountinfo import AccountInfo
from .context import Context
from .group import Group
from .loadedmarket import LoadedMarket
from .lotsizeconverter import LotSizeConverter, RaisingLotSizeConverter
from .market import Market, InventorySource
from .observables import DisposingSubject, observable_pipeline_error_reporter
from .orderbookside import PerpOrderBookSide
from .orders import Order
from .perpeventqueue import PerpEvent, PerpEventQueue, UnseenPerpEventChangesTracker
from .perpmarketdetails import PerpMarketDetails
from .token import Instrument, Token


# # 🥭 FundingRate class
#
# A simple way to package details of a funding rate in a single object.
#
class FundingRate(typing.NamedTuple):
    symbol: str
    rate: Decimal
    oracle_price: Decimal
    open_interest: Decimal
    from_: datetime
    to: datetime

    @staticmethod
    def from_stats_data(symbol: str, lot_size_converter: LotSizeConverter, oldest_stats: typing.Dict[str, typing.Any], newest_stats: typing.Dict[str, typing.Any]) -> "FundingRate":
        oldest_short_funding = Decimal(oldest_stats["shortFunding"])
        oldest_long_funding = Decimal(oldest_stats["longFunding"])
        oldest_oracle_price = Decimal(oldest_stats["baseOraclePrice"])
        from_timestamp = parser.parse(oldest_stats["time"]).replace(microsecond=0)

        newest_short_funding = Decimal(newest_stats["shortFunding"])
        newest_long_funding = Decimal(newest_stats["longFunding"])
        newest_oracle_price = Decimal(newest_stats["baseOraclePrice"])
        to_timestamp = parser.parse(newest_stats["time"]).replace(microsecond=0)
        raw_open_interest = Decimal(newest_stats["openInterest"])
        open_interest = lot_size_converter.base_size_lots_to_number(raw_open_interest) / 2

        average_oracle_price = (oldest_oracle_price + newest_oracle_price) / 2
        average_oracle_price = newest_oracle_price

        start_funding = (oldest_long_funding + oldest_short_funding) / 2
        end_funding = (newest_long_funding + newest_short_funding) / 2
        funding_difference = end_funding - start_funding

        funding_in_quote_decimals = lot_size_converter.quote.shift_to_decimals(funding_difference)

        base_price_in_base_lots = average_oracle_price * lot_size_converter.lot_size
        funding_rate = funding_in_quote_decimals / base_price_in_base_lots
        return FundingRate(symbol=symbol, rate=funding_rate, oracle_price=average_oracle_price, open_interest=open_interest, from_=from_timestamp, to=to_timestamp)

    def __str__(self) -> str:
        return f"« FundingRate {self.symbol} {self.rate:,.8%}, open interest: {self.open_interest:,.8f} from: {self.from_} to {self.to} »"

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 PerpMarket class
#
# This class encapsulates our knowledge of a Mango perps market.
#
class PerpMarket(LoadedMarket):
    def __init__(self, mango_program_address: PublicKey, address: PublicKey, base: Instrument, quote: Token,
                 underlying_perp_market: PerpMarketDetails) -> None:
        super().__init__(mango_program_address, address, InventorySource.ACCOUNT, base, quote, RaisingLotSizeConverter())
        self.underlying_perp_market: PerpMarketDetails = underlying_perp_market
        self.lot_size_converter: LotSizeConverter = LotSizeConverter(
            base, underlying_perp_market.base_lot_size, quote, underlying_perp_market.quote_lot_size)

    @property
    def symbol(self) -> str:
        return f"{self.base.symbol}-PERP"

    @property
    def group(self) -> Group:
        return self.underlying_perp_market.group

    @property
    def bids_address(self) -> PublicKey:
        return self.underlying_perp_market.bids

    @property
    def asks_address(self) -> PublicKey:
        return self.underlying_perp_market.asks

    def parse_account_info_to_orders(self, account_info: AccountInfo) -> typing.Sequence[Order]:
        side: PerpOrderBookSide = PerpOrderBookSide.parse(account_info, self.underlying_perp_market)
        return side.orders()

    def fetch_funding(self, context: Context) -> FundingRate:
        stats = context.fetch_stats(f"perp/funding_rate?mangoGroup={self.group.name}&market={self.symbol}")
        newest_stats = stats[0]
        oldest_stats = stats[-1]

        return FundingRate.from_stats_data(self.symbol, self.lot_size_converter, oldest_stats, newest_stats)

    def unprocessed_events(self, context: Context) -> typing.Sequence[PerpEvent]:
        event_queue: PerpEventQueue = PerpEventQueue.load(
            context, self.underlying_perp_market.event_queue, self.lot_size_converter)
        return event_queue.unprocessed_events

    def accounts_to_crank(self, context: Context, additional_account_to_crank: typing.Optional[PublicKey]) -> typing.Sequence[PublicKey]:
        accounts_to_crank: typing.List[PublicKey] = []
        for event_to_crank in self.unprocessed_events(context):
            accounts_to_crank += event_to_crank.accounts_to_crank

        if additional_account_to_crank is not None:
            accounts_to_crank += [additional_account_to_crank]

        seen = []
        distinct = []
        for account in accounts_to_crank:
            account_str = account.to_base58()
            if account_str not in seen:
                distinct += [account]
                seen += [account_str]
        distinct.sort(key=lambda address: address._key or [0])
        return distinct

    def observe_events(self, context: Context, interval: int = 30) -> DisposingSubject:
        perp_event_queue: PerpEventQueue = PerpEventQueue.load(
            context, self.underlying_perp_market.event_queue, self.lot_size_converter)
        perp_splitter: UnseenPerpEventChangesTracker = UnseenPerpEventChangesTracker(perp_event_queue)

        fill_events = DisposingSubject()
        disposable_subscription = rx.interval(interval).pipe(
            ops.observe_on(context.create_thread_pool_scheduler()),
            ops.start_with(-1),
            ops.map(lambda _: PerpEventQueue.load(
                context, self.underlying_perp_market.event_queue, self.lot_size_converter)),
            ops.flat_map(perp_splitter.unseen),
            ops.catch(observable_pipeline_error_reporter),
            ops.retry()
        ).subscribe(fill_events)
        fill_events.add_disposable(disposable_subscription)
        return fill_events

    def __str__(self) -> str:
        underlying: str = f"{self.underlying_perp_market}".replace("\n", "\n    ")
        return f"""« PerpMarket {self.symbol} {self.address} [{self.program_address}]
    {underlying}
»"""


# # 🥭 PerpMarketStub class
#
# This class holds information to load a `PerpMarket` object but doesn't automatically load it.
#
class PerpMarketStub(Market):
    def __init__(self, mango_program_address: PublicKey, address: PublicKey, base: Instrument, quote: Token,
                 group_address: PublicKey) -> None:
        super().__init__(mango_program_address, address, InventorySource.ACCOUNT, base, quote, RaisingLotSizeConverter())
        self.group_address: PublicKey = group_address

    def load(self, context: Context, group: typing.Optional[Group] = None) -> PerpMarket:
        actual_group: Group = group or Group.load(context, self.group_address)
        underlying_perp_market: PerpMarketDetails = PerpMarketDetails.load(context, self.address, actual_group)
        return PerpMarket(self.program_address, self.address, self.base, self.quote, underlying_perp_market)

    @property
    def symbol(self) -> str:
        return f"{self.base.symbol}-PERP"

    def __str__(self) -> str:
        return f"« PerpMarketStub {self.symbol} {self.address} [{self.program_address}] »"
