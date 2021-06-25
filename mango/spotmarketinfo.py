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

from decimal import Decimal
from solana.publickey import PublicKey

from .layouts import layouts
from .marketlookup import MarketLookup


# # 🥭 SpotMarketInfo class
#


class SpotMarketInfo():
    def __init__(self, address: PublicKey, maint_asset_weight: Decimal, init_asset_weight: Decimal, maint_liab_weight: Decimal, init_liab_weight: Decimal):
        self.address: PublicKey = address
        self.maint_asset_weight: Decimal = maint_asset_weight
        self.init_asset_weight: Decimal = init_asset_weight
        self.maint_liab_weight: Decimal = maint_liab_weight
        self.init_liab_weight: Decimal = init_liab_weight

    def from_layout(layout: layouts.SPOT_MARKET_INFO, market_lookup: MarketLookup) -> "SpotMarketInfo":
        return SpotMarketInfo(layout.spot_market, layout.maint_asset_weight, layout.init_asset_weight, layout.maint_liab_weight, layout.init_liab_weight)

    def from_layout_or_none(layout: layouts.SPOT_MARKET_INFO, market_lookup: MarketLookup) -> typing.Optional["SpotMarketInfo"]:
        if layout.spot_market is None:
            return None

        return SpotMarketInfo.from_layout(layout, market_lookup)

    def __str__(self):
        return f"""« 𝚂𝚙𝚘𝚝𝙼𝚊𝚛𝚔𝚎𝚝𝙸𝚗𝚏𝚘 [{self.address}]
    Asset Weights: {self.init_asset_weight} / {self.maint_asset_weight}
    Liability Weights: {self.init_liab_weight} / {self.maint_liab_weight}
»"""

    def __repr__(self) -> str:
        return f"{self}"
