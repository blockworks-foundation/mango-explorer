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

from decimal import Decimal
from pyserum.market import Market
from solana.publickey import PublicKey

from .baskettoken import BasketToken
from .context import Context
from .spotmarket import SpotMarket

# # 🥭 MarketMetadata class
#


class MarketMetadata:
    def __init__(self, name: str, address: PublicKey, base: BasketToken, quote: BasketToken,
                 spot: SpotMarket, oracle: PublicKey, decimals: Decimal):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.name: str = name
        self.address: PublicKey = address
        self.base: BasketToken = base
        self.quote: BasketToken = quote
        self.spot: SpotMarket = spot
        self.oracle: PublicKey = oracle
        self.decimals: Decimal = decimals
        self.symbol: str = f"{base.token.symbol}/{quote.token.symbol}"
        self._market = None

    def fetch_market(self, context: Context) -> Market:
        if self._market is None:
            self._market = Market.load(context.client, self.spot.address)

        return self._market

    def __str__(self) -> str:
        base = f"{self.base}".replace("\n", "\n    ")
        quote = f"{self.quote}".replace("\n", "\n    ")
        return f"""« Market '{self.name}' [{self.address}/{self.spot.address}]:
    Base: {base}
    Quote: {quote}
    Oracle: {self.oracle} ({self.decimals} decimals)
»"""

    def __repr__(self) -> str:
        return f"{self}"
