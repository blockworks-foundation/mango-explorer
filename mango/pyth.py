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
import typing

from datetime import datetime
from decimal import Decimal
from solana.publickey import PublicKey

from .accountinfo import AccountInfo
from .context import Context
from .market import Market
from .oracles import Oracle, OracleFactory, OracleSource, Price

# Use this for Pyth V1.
from .pythnetwork import pythnetwork_v1 as pythnetwork

# Use this for Pyth V2.
# from .pythnetwork import pythnetwork


# # 🥭 Pyth
#
# This file contains code specific to the [Pyth Network](https://pyth.network/).
#


# # 🥭 PythOracle class
#
# Implements the `Oracle` abstract base class specialised to the Pyth Network.
#

class PythOracle(Oracle):
    def __init__(self, market: Market, product_data: pythnetwork.PRODUCT):
        name = f"Pyth Oracle for {market.symbol}"
        super().__init__(name, market)
        self.market: Market = market
        self.product_data: pythnetwork.PRODUCT = product_data
        self.address: PublicKey = product_data.address
        self.source: OracleSource = OracleSource(name, "pyth", market)

    def fetch_price(self, context: Context) -> Price:
        price_account_info = AccountInfo.load(context, self.product_data.px_acc)
        if price_account_info is None:
            raise Exception(f"Price account {self.product_data.px_acc} not found.")

        if len(price_account_info.data) != pythnetwork.PRICE.sizeof():
            raise Exception(
                f"Price account data has incorrect size. Expected: {pythnetwork.PRICE.sizeof()}, got {len(price_account_info.data)}.")

        price_data = pythnetwork.PRICE.parse(price_account_info.data)
        if price_data.magic != pythnetwork.MAGIC:
            raise Exception(f"Price account {price_account_info.address} is not a Pyth account.")

        factor = Decimal(10) ** price_data.expo
        price = price_data.agg.price * factor
        return Price(self.source, datetime.now(), self.market, price)


# # 🥭 PythOracleFactory class
#
# Implements the `OracleFactory` abstract base class specialised to the Pyth Network.
#

class PythOracleFactory(OracleFactory):
    def __init__(self, address: PublicKey = pythnetwork.PYTH_MAPPING_ROOT) -> None:
        super().__init__(f"Pyth Oracle Factory [{address}]")
        self.address = address

    def oracle_for_market(self, context: Context, market: Market) -> typing.Optional[Oracle]:
        pyth_symbol = self._market_symbol_to_pyth_symbol(market.symbol)
        products = self._fetch_all_pyth_products(context, self.address)
        for product in products:
            if product.attr["symbol"] == pyth_symbol:
                return PythOracle(market, product)
        return None

    def all_available_symbols(self, context: Context) -> typing.List[str]:
        products = self._fetch_all_pyth_products(context, self.address)
        symbols: typing.List[str] = []
        for product in products:
            symbol = product.attr["symbol"]
            symbols += self._pyth_symbol_to_market_symbols(symbol)
        return symbols

    def _market_symbol_to_pyth_symbol(self, symbol: str) -> str:
        normalised = symbol.upper()
        fixed_usdt = re.sub('USDT$', 'USD', normalised)
        return re.sub('USDC$', 'USD', fixed_usdt)

    def _pyth_symbol_to_market_symbols(self, symbol: str) -> typing.List[str]:
        if symbol.endswith("USD"):
            return [f"{symbol}C", f"{symbol}T"]
        return [symbol]

    def _load_pyth_mapping(self, context: Context, address: PublicKey) -> pythnetwork.MAPPING:
        account_info = AccountInfo.load(context, address)
        if account_info is None:
            raise Exception(f"Pyth mapping account {address} not found.")

        if len(account_info.data) != pythnetwork.MAPPING.sizeof():
            raise Exception(
                f"Mapping account data has incorrect size. Expected: {pythnetwork.MAPPING.sizeof()}, got {len(account_info.data)}.")

        mapping = pythnetwork.MAPPING.parse(account_info.data)
        mapping.address = account_info.address
        if mapping.magic != pythnetwork.MAGIC:
            raise Exception(f"Mapping account {account_info.address} is not a Pyth account.")

        return mapping

    def _fetch_all_pyth_products(self, context: Context, address: PublicKey) -> typing.List[typing.Any]:
        mapping = self._load_pyth_mapping(context, address)
        all_product_addresses = mapping.products[0:int(mapping.num)]
        product_account_infos = AccountInfo.load_multiple(context, all_product_addresses)
        products: typing.List[pythnetwork.PRODUCT] = []
        for product_account_info in product_account_infos:
            product = pythnetwork.PRODUCT.parse(product_account_info.data)
            product.address = product_account_info.address
            if product.magic != pythnetwork.MAGIC:
                raise Exception(f"Product account {product_account_info.address} is not a Pyth account.")
            products += [product]
        return products
