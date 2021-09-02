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


import re
import rx
import rx.operators as ops
import typing

from datetime import datetime
from decimal import Decimal
from solana.publickey import PublicKey

from ...accountinfo import AccountInfo
from ...context import Context
from ...market import Market
from ...observables import observable_pipeline_error_reporter
from ...oracle import Oracle, OracleProvider, OracleSource, Price, SupportedOracleFeature

from .layouts import MAGIC, MAPPING, PRICE, PRODUCT, PYTH_DEVNET_MAPPING_ROOT, PYTH_MAINNET_MAPPING_ROOT


# # 🥭 Pyth
#
# This file contains code specific to the [Pyth Network](https://pyth.network/).
#
# ## Pyth's Confidence Interval
#
# It seems to akin to a spread, and always specified in the quote currency.
#
# Pyth Medium article:
# https://pythnetwork.medium.com/what-is-confidence-uncertainty-in-a-price-649583b598cf
#
# From Discord: https://discord.com/channels/826115122799837205/861627739975319602/861903479331880981
# 6/ What does Pyth's confidence value mean when provided with the price?
# → Confidence is a function of where one expects a trade to occur from the "true" price, i.e. what is the potential dispersion estimation?
#
# From Discord: https://discord.com/channels/826115122799837205/826115122799837208/858091212980092978
# [T]he confidence value here is how far from the aggregate price we believe the true price might be. It
# reflects a combination of the uncertainty of individual quoters and how well individual quoters agree
# with each other
#


# # 🥭 PythOracle class
#
# Implements the `Oracle` abstract base class specialised to the Pyth Network.
#

class PythOracle(Oracle):
    def __init__(self, context: Context, market: Market, product_data: typing.Any):
        name = f"Pyth Oracle for {market.symbol}"
        super().__init__(name, market)
        self.context: Context = context
        self.market: Market = market
        self.product_data: typing.Any = product_data
        self.address: PublicKey = product_data.address
        features: SupportedOracleFeature = SupportedOracleFeature.MID_PRICE | SupportedOracleFeature.CONFIDENCE
        self.source: OracleSource = OracleSource("Pyth", name, features, market)

    def fetch_price(self, _: Context) -> Price:
        price_account_info = AccountInfo.load(self.context, self.product_data.px_acc)
        if price_account_info is None:
            raise Exception(f"[{self.context.name}] Price account {self.product_data.px_acc} not found.")

        if len(price_account_info.data) != PRICE.sizeof():
            raise Exception(
                f"[{self.context.name}] Price account data has incorrect size. Expected: {PRICE.sizeof()}, got {len(price_account_info.data)}.")

        price_data = PRICE.parse(price_account_info.data)
        if price_data.magic != MAGIC:
            raise Exception(f"[{self.context.name}] Price account {price_account_info.address} is not a Pyth account.")

        factor = Decimal(10) ** price_data.expo
        price = price_data.agg.price * factor
        confidence = price_data.agg.conf * factor

        # Pyth has no notion of bids, asks, or spreads so just provide the single price.
        return Price(self.source, datetime.now(), self.market, price, price, price, confidence)

    def to_streaming_observable(self, context: Context) -> rx.core.Observable:
        return rx.interval(1).pipe(
            ops.observe_on(context.create_thread_pool_scheduler()),
            ops.start_with(-1),
            ops.map(lambda _: self.fetch_price(context)),
            ops.catch(observable_pipeline_error_reporter),
            ops.retry(),
        )


# # 🥭 PythOracleProvider class
#
# Implements the `OracleProvider` abstract base class specialised to the Pyth Network.
#
# In order to allow it to vary its cluster without affecting other programs, this takes a `Context` in its
# constructor and uses that to access the data. It ignores the context passed as a parameter to its methods.
# This allows the context-fudging to only happen on construction.

class PythOracleProvider(OracleProvider):
    def __init__(self, context: Context) -> None:
        self.address: PublicKey = PYTH_MAINNET_MAPPING_ROOT if context.client.cluster_name == "mainnet" else PYTH_DEVNET_MAPPING_ROOT
        super().__init__(f"Pyth Oracle Factory [{self.address}]")
        self.context: Context = context

    def oracle_for_market(self, _: Context, market: Market) -> typing.Optional[Oracle]:
        pyth_symbol = self._market_symbol_to_pyth_symbol(market.symbol)
        products = self._fetch_all_pyth_products(self.context, self.address)
        for product in products:
            if product.attr["symbol"] == pyth_symbol:
                return PythOracle(self.context, market, product)
        return None

    def all_available_symbols(self, _: Context) -> typing.Sequence[str]:
        products = self._fetch_all_pyth_products(self.context, self.address)
        symbols: typing.List[str] = []
        for product in products:
            symbol = product.attr["symbol"]
            symbols += self._pyth_symbol_to_market_symbols(symbol)
        return symbols

    def _market_symbol_to_pyth_symbol(self, symbol: str) -> str:
        normalised = symbol.upper()
        fixed_usdt = re.sub("USDT$", "USD", normalised)
        fixed_usdc = re.sub("USDC$", "USD", fixed_usdt)
        fixed_perp = re.sub("\\-PERP$", "/USD", fixed_usdc)
        return fixed_perp

    def _pyth_symbol_to_market_symbols(self, symbol: str) -> typing.Sequence[str]:
        if symbol.endswith("USD"):
            return [f"{symbol}C", f"{symbol}T"]
        return [symbol]

    def _load_pyth_mapping(self, context: Context, address: PublicKey) -> typing.Any:
        account_info = AccountInfo.load(context, address)
        if account_info is None:
            raise Exception(f"[{context.name}] Pyth mapping account {address} not found.")

        if len(account_info.data) != MAPPING.sizeof():
            raise Exception(
                f"Mapping account data has incorrect size. Expected: {MAPPING.sizeof()}, got {len(account_info.data)}.")

        mapping: typing.Any = MAPPING.parse(account_info.data)
        mapping.address = account_info.address
        if mapping.magic != MAGIC:
            raise Exception(f"[{context.name}] Mapping account {account_info.address} is not a Pyth account.")

        return mapping

    def _fetch_all_pyth_products(self, context: Context, address: PublicKey) -> typing.Sequence[typing.Any]:
        mapping = self._load_pyth_mapping(context, address)
        all_product_addresses = mapping.products[0:int(mapping.num)]
        product_account_infos = AccountInfo.load_multiple(context, all_product_addresses)
        products: typing.List[typing.Any] = []
        for product_account_info in product_account_infos:
            product: typing.Any = PRODUCT.parse(product_account_info.data)
            product.address = product_account_info.address
            if product.magic != MAGIC:
                raise Exception(
                    f"[{context.name}] Product account {product_account_info.address} is not a Pyth account.")
            products += [product]
        return products
