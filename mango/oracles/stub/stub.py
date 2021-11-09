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
from solana.publickey import PublicKey

from ...cache import Cache
from ...context import Context
from ...ensuremarketloaded import ensure_market_loaded
from ...market import Market
from ...observables import observable_pipeline_error_reporter
from ...oracle import Oracle, OracleProvider, OracleSource, Price, SupportedOracleFeature
from ...perpmarket import PerpMarket
from ...spotmarket import SpotMarket


# # 🥭 Stub
#
# This file contains code specific to oracles on the Mango Stub Oracle.
#


# # 🥭 StubOracleConfidence constant
#
# The stub oracle doesn't provide a confidence value.
#

StubOracleConfidence: Decimal = Decimal(0)


# # 🥭 StubOracle class
#
# Implements the `Oracle` abstract base class specialised to the Stub Oracle.
#


class StubOracle(Oracle):
    def __init__(self, market: Market, index: int, cache_address: PublicKey) -> None:
        name = f"Stub Oracle for {market.symbol}"
        super().__init__(name, market)
        self.index: int = index
        self.cache_address: PublicKey = cache_address
        features: SupportedOracleFeature = SupportedOracleFeature.MID_PRICE
        self.source: OracleSource = OracleSource("Stub Oracle", name, features, market)

    def fetch_price(self, context: Context) -> Price:
        cache: Cache = Cache.load(context, self.cache_address)
        raw_price = cache.price_cache[self.index]
        if raw_price is None:
            raise Exception(f"Stub Oracle does not contain a price for market {self.symbol} at index {self.index}.")
        # Should convert raw_price to actual price.
        # Discord on stub price from lagzda:
        #   https://discord.com/channels/791995070613159966/853370356244152360/871871877382033478
        # "Hey, related to the conversation above since we should be reporting native quote per native
        # base I did the incorrect change. Instead of adjusting RAY etc stub oracles prices from 2 to
        # 2_000_000, I should've adjusted the Pyth oracles prices which soon will be deployed. That
        # will give you the consistent results, but you'll need to adjust your code"
        return Price(self.source, datetime.now(), self.market, raw_price.price, raw_price.price, raw_price.price, StubOracleConfidence)

    def to_streaming_observable(self, context: Context) -> rx.core.typing.Observable[Price]:
        prices = rx.interval(1).pipe(
            ops.observe_on(context.create_thread_pool_scheduler()),
            ops.start_with(-1),
            ops.map(lambda _: self.fetch_price(context)),
            ops.catch(observable_pipeline_error_reporter),
            ops.retry(),
        )
        return typing.cast(rx.core.typing.Observable[Price], prices)


# # 🥭 StubOracleProvider class
#
# Implements the `OracleProvider` abstract base class specialised to the Serum Network.
#

class StubOracleProvider(OracleProvider):
    def __init__(self) -> None:
        super().__init__("Stub Oracle Factory")

    def oracle_for_market(self, context: Context, market: Market) -> typing.Optional[Oracle]:
        loaded_market: Market = ensure_market_loaded(context, market)
        if isinstance(loaded_market, SpotMarket):
            spot_index: int = loaded_market.group.slot_by_spot_market_address(loaded_market.address).index
            return StubOracle(loaded_market, spot_index, loaded_market.group.cache)
        elif isinstance(loaded_market, PerpMarket):
            perp_index: int = loaded_market.group.slot_by_perp_market_address(loaded_market.address).index
            return StubOracle(loaded_market, perp_index, loaded_market.group.cache)

        return None

    def all_available_symbols(self, context: Context) -> typing.Sequence[str]:
        all_markets = context.market_lookup.all_markets()
        symbols: typing.List[str] = []
        for market in all_markets:
            symbols += [market.symbol]
        return symbols
