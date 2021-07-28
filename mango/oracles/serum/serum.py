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
from solana.rpc.api import Client

from ...context import Context
from ...ensuremarketloaded import ensure_market_loaded
from ...market import Market
from ...observables import observable_pipeline_error_reporter
from ...oracle import Oracle, OracleProvider, OracleSource, Price, SupportedOracleFeature
from ...orders import Order, Side
from ...serummarket import SerumMarket, SerumMarketStub
from ...serummarketlookup import SerumMarketLookup
from ...spltokenlookup import SplTokenLookup
from ...spotmarket import SpotMarket, SpotMarketStub


# # 🥭 Serum
#
# This file contains code specific to oracles on the [Serum DEX](https://projectserum.com/).
#


# # 🥭 FtxOracleConfidence constant
#
# FTX doesn't provide a confidence value.
#

SerumOracleConfidence: Decimal = Decimal(0)


# # 🥭 SerumOracle class
#
# Implements the `Oracle` abstract base class specialised to the Serum DEX.
#


class SerumOracle(Oracle):
    def __init__(self, market: SerumMarket):
        name = f"Serum Oracle for {market.symbol}"
        super().__init__(name, market)
        self.market: SerumMarket = market
        features: SupportedOracleFeature = SupportedOracleFeature.TOP_BID_AND_OFFER
        self.source: OracleSource = OracleSource("Serum", name, features, market)

    def fetch_price(self, context: Context) -> Price:
        # TODO: Do this right?
        context = copy.copy(context)
        context.cluster = "mainnet-beta"
        context.cluster_url = "https://solana-api.projectserum.com"
        context.client = Client(context.cluster_url)
        mainnet_serum_market_lookup: SerumMarketLookup = SerumMarketLookup.load(SplTokenLookup.DefaultDataFilepath)
        adjusted_market = self.market
        mainnet_adjusted_market: typing.Optional[Market] = mainnet_serum_market_lookup.find_by_symbol(
            self.market.symbol)
        if mainnet_adjusted_market is not None:
            adjusted_market_stub = typing.cast(SerumMarketStub, mainnet_adjusted_market)
            adjusted_market = adjusted_market_stub.load(context)

        orders: typing.Sequence[Order] = adjusted_market.orders(context)
        top_bid = max([order.price for order in orders if order.side == Side.BUY])
        top_ask = min([order.price for order in orders if order.side == Side.SELL])
        mid_price = (top_bid + top_ask) / 2

        return Price(self.source, datetime.now(), self.market, top_bid, mid_price, top_ask, SerumOracleConfidence)

    def to_streaming_observable(self, context: Context) -> rx.core.typing.Observable:
        return rx.interval(1).pipe(
            ops.observe_on(context.pool_scheduler),
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
        loaded_market: Market = ensure_market_loaded(context, market)
        if isinstance(loaded_market, SpotMarket):
            serum_market = SerumMarket(loaded_market.address, loaded_market.base,
                                       loaded_market.quote, loaded_market.underlying_serum_market)
            return SerumOracle(serum_market)
        elif isinstance(loaded_market, SerumMarket):
            return SerumOracle(loaded_market)
        else:
            fixed_symbol = self._market_symbol_to_serum_symbol(loaded_market.symbol)
            underlying_market = context.market_lookup.find_by_symbol(fixed_symbol)
            if underlying_market is None:
                return None
            if isinstance(underlying_market, SpotMarketStub) or isinstance(underlying_market, SpotMarket) or isinstance(underlying_market, SerumMarketStub) or isinstance(underlying_market, SerumMarket):
                return self.oracle_for_market(context, underlying_market)

        return None

    def all_available_symbols(self, context: Context) -> typing.Sequence[str]:
        all_markets = context.market_lookup.all_markets()
        symbols: typing.List[str] = []
        for market in all_markets:
            symbols += [market.symbol]
        return symbols

    def _market_symbol_to_serum_symbol(self, symbol: str) -> str:
        normalised = symbol.upper()
        fixed_perp = re.sub("\\-PERP$", "/USDC", normalised)
        return fixed_perp
