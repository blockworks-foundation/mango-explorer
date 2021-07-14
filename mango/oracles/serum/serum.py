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


import copy
import re
import rx
import rx.operators as ops
import typing

from datetime import datetime
from decimal import Decimal
from pyserum.market.orderbook import OrderBook
from pyserum.market import Market as RawSerumMarket
from solana.rpc.api import Client

from ...accountinfo import AccountInfo
from ...context import Context
from ...market import AddressableMarket, Market
from ...observables import observable_pipeline_error_reporter
from ...oracle import Oracle, OracleProvider, OracleSource, Price
from ...serummarket import SerumMarket
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
    def __init__(self, market: AddressableMarket):
        name = f"Serum Oracle for {market.symbol}"
        super().__init__(name, market)
        self.market: AddressableMarket = market
        self.source: OracleSource = OracleSource("Serum", name, market)
        self._serum_market: RawSerumMarket = None

    def fetch_price(self, context: Context) -> Price:
        # TODO: Do this right?
        context = copy.copy(context)
        context.cluster = "mainnet-beta"
        context.cluster_url = "https://solana-api.projectserum.com"
        context.client = Client(context.cluster_url)
        if self._serum_market is None:
            self._serum_market = RawSerumMarket.load(context.client, self.market.address, context.dex_program_id)

        bids_address = self._serum_market.state.bids()
        asks_address = self._serum_market.state.asks()
        bid_ask_account_infos = AccountInfo.load_multiple(context, [bids_address, asks_address])
        if len(bid_ask_account_infos) != 2:
            raise Exception(
                f"Failed to get bid/ask data from Serum for market address {self.market.address} (bids: {bids_address}, asks: {asks_address}).")
        bids = OrderBook.from_bytes(self._serum_market.state, bid_ask_account_infos[0].data)
        asks = OrderBook.from_bytes(self._serum_market.state, bid_ask_account_infos[1].data)

        top_bid = list(bids.orders())[-1]
        top_ask = list(asks.orders())[0]
        top_bid_price = self.market.quote.round(Decimal(top_bid.info.price))
        top_ask_price = self.market.quote.round(Decimal(top_ask.info.price))
        mid_price = (top_bid_price + top_ask_price) / 2

        return Price(self.source, datetime.now(), self.market, top_bid_price, mid_price, top_ask_price)

    def to_streaming_observable(self, context: Context) -> rx.core.typing.Observable:
        context.cluster = "mainnet-beta"
        context.cluster_url = "https://solana-api.projectserum.com"
        context.client = Client(context.cluster_url)
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
        elif isinstance(market, SerumMarket):
            return SerumOracle(market)
        else:
            fixed_symbol = self._market_symbol_to_serum_symbol(market.symbol)
            underlying_market = context.market_lookup.find_by_symbol(fixed_symbol)
            if underlying_market is None:
                return None
            if isinstance(underlying_market, SpotMarket) or isinstance(underlying_market, SerumMarket):
                return SerumOracle(underlying_market)

        return None

    def all_available_symbols(self, context: Context) -> typing.Sequence[str]:
        all_markets = context.market_lookup.all_markets()
        symbols: typing.List[str] = []
        for market in all_markets:
            symbols += [market.symbol]
        return symbols

    def _market_symbol_to_serum_symbol(self, symbol: str) -> str:
        normalised = symbol.upper()
        fixed_perp = re.sub('\-PERP$', '/USDC', normalised)
        return fixed_perp
