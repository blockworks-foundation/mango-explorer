# # ⚠ Warning
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
# NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# [🥭 Mango Markets](https://markets/) support is available at:
#   [Docs](https://docs.markets/)
#   [Discord](https://discord.gg/67jySBhxrg)
#   [Twitter](https://twitter.com/mangomarkets)
#   [Github](https://github.com/blockworks-foundation)
#   [Email](mailto:hello@blockworks.foundation)


import rx
import rx.operators as ops
import typing

from datetime import datetime
from decimal import Decimal
from pyserum.market.orderbook import OrderBook
from pyserum.market import Market as SerumMarket

from ...accountinfo import AccountInfo
from ...context import Context
from ...market import Market
from ...observables import observable_pipeline_error_reporter
from ...oracle import Oracle, OracleProvider, OracleSource, Price
from ...spotmarket import SpotMarket


# # 🥭 Serum
#
# This file contains code specific to oracles on the [Serum DEX](https://projectserum.com/).
#


# # 🥭 SerumOracle class
#
# Implements the `Oracle` abstract base class specialised to the Serum DEX.
#

class SerumOracle(Oracle):
    def __init__(self, spot_market: SpotMarket):
        name = f"Serum Oracle for {spot_market.symbol}"
        super().__init__(name, spot_market)
        self.spot_market: SpotMarket = spot_market
        self.source: OracleSource = OracleSource("Serum", name, spot_market)
        self._serum_market: SerumMarket = None

    def fetch_price(self, context: Context) -> Price:
        if self._serum_market is None:
            self._serum_market = SerumMarket.load(context.client, self.spot_market.address, context.dex_program_id)

        bids_address = self._serum_market.state.bids()
        asks_address = self._serum_market.state.asks()
        bid_ask_account_infos = AccountInfo.load_multiple(context, [bids_address, asks_address])
        if len(bid_ask_account_infos) != 2:
            raise Exception(
                f"Failed to get bid/ask data from Serum for market address {self.spot_market.address} (bids: {bids_address}, asks: {asks_address}).")
        bids = OrderBook.from_bytes(self._serum_market.state, bid_ask_account_infos[0].data)
        asks = OrderBook.from_bytes(self._serum_market.state, bid_ask_account_infos[1].data)

        top_bid = list(bids.orders())[-1]
        top_ask = list(asks.orders())[0]
        top_bid_price = self.spot_market.quote.round(Decimal(top_bid.info.price))
        top_ask_price = self.spot_market.quote.round(Decimal(top_ask.info.price))
        mid_price = (top_bid_price + top_ask_price) / 2

        return Price(self.source, datetime.now(), self.spot_market, top_bid_price, mid_price, top_ask_price)

    def to_streaming_observable(self, context: Context) -> rx.core.typing.Observable:
        return rx.interval(1).pipe(
            ops.subscribe_on(context.pool_scheduler),
            ops.start_with(-1),
            ops.map(lambda _: self.fetch_price(context)),
            ops.catch(observable_pipeline_error_reporter),
            ops.retry(),
        )


# # 🥭 SerumOracleProvider class
#
# Implements the `OracleProvider` abstract base class specialised to the Serum Network.
#

class SerumOracleProvider(OracleProvider):
    def __init__(self) -> None:
        super().__init__("Serum Oracle Factory")

    def oracle_for_market(self, context: Context, market: Market) -> typing.Optional[Oracle]:
        if isinstance(market, SpotMarket):
            return SerumOracle(market)
        else:
            optional_spot_market = context.market_lookup.find_by_symbol(market.symbol)
            if optional_spot_market is None:
                return None
            if isinstance(optional_spot_market, SpotMarket):
                return SerumOracle(optional_spot_market)

        return None

    def all_available_symbols(self, context: Context) -> typing.Sequence[str]:
        all_markets = context.market_lookup.all_markets()
        symbols: typing.List[str] = []
        for spot_market in all_markets:
            symbols += [spot_market.symbol]
        return symbols
