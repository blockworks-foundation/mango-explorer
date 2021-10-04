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

from .constants import SYSTEM_PROGRAM_ADDRESS


# # 🥭 SpotMarketInfo class
#
class SpotMarketInfo():
    def __init__(self, address: PublicKey, maint_asset_weight: Decimal, init_asset_weight: Decimal, maint_liab_weight: Decimal, init_liab_weight: Decimal):
        self.address: PublicKey = address
        self.maint_asset_weight: Decimal = maint_asset_weight
        self.init_asset_weight: Decimal = init_asset_weight
        self.maint_liab_weight: Decimal = maint_liab_weight
        self.init_liab_weight: Decimal = init_liab_weight

    def from_layout(layout: typing.Any) -> "SpotMarketInfo":
        spot_market: PublicKey = layout.spot_market
        maint_asset_weight: Decimal = round(layout.maint_asset_weight, 8)
        init_asset_weight: Decimal = round(layout.init_asset_weight, 8)
        maint_liab_weight: Decimal = round(layout.maint_liab_weight, 8)
        init_liab_weight: Decimal = round(layout.init_liab_weight, 8)
        return SpotMarketInfo(spot_market, maint_asset_weight, init_asset_weight, maint_liab_weight, init_liab_weight)

    def from_layout_or_none(layout: typing.Any) -> typing.Optional["SpotMarketInfo"]:
        if (layout.spot_market is None) or (layout.spot_market == SYSTEM_PROGRAM_ADDRESS):
            return None

        return SpotMarketInfo.from_layout(layout)

    def __str__(self) -> str:
        return f"""« 𝚂𝚙𝚘𝚝𝙼𝚊𝚛𝚔𝚎𝚝𝙸𝚗𝚏𝚘 [{self.address}]
    Asset Weights:
        Initial: {self.init_asset_weight}
        Maintenance: {self.maint_asset_weight}
    Liability Weights:
        Initial: {self.init_liab_weight}
        Maintenance: {self.maint_liab_weight}
»"""

    def __repr__(self) -> str:
        return f"{self}"
