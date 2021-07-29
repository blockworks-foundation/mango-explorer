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


from decimal import Decimal

from .layouts import layouts
from .perpopenorders import PerpOpenOrders


# # 🥭 PerpAccount class
#
# Perp accounts aren't directly addressable. They exist as a sub-object of a full Mango `Account` object.
#
class PerpAccount:
    def __init__(self, base_position: Decimal, quote_position: Decimal, long_settled_funding: Decimal,
                 short_settled_funding: Decimal, mngo_accrued: Decimal, open_orders: PerpOpenOrders):
        self.base_position: Decimal = base_position
        self.quote_position: Decimal = quote_position
        self.long_settled_funding: Decimal = long_settled_funding
        self.short_settled_funding: Decimal = short_settled_funding
        self.mngo_accrued: Decimal = mngo_accrued
        self.open_orders: PerpOpenOrders = open_orders

    @staticmethod
    def from_layout(layout: layouts.PERP_ACCOUNT) -> "PerpAccount":
        base_position: Decimal = layout.base_position
        quote_position: Decimal = layout.quote_position
        long_settled_funding: Decimal = layout.long_settled_funding
        short_settled_funding: Decimal = layout.short_settled_funding
        mngo_accrued: Decimal = layout.mngo_accrued

        open_orders: PerpOpenOrders = PerpOpenOrders.from_layout(layout.open_orders)

        return PerpAccount(base_position, quote_position, long_settled_funding, short_settled_funding, mngo_accrued, open_orders)

    def __str__(self) -> str:
        open_orders = f"{self.open_orders}".replace("\n", "\n        ")
        return f"""« 𝙿𝚎𝚛𝚙𝙰𝚌𝚌𝚘𝚞𝚗𝚝
    Base Position: {self.base_position}
    Quote Position: {self.quote_position}
    Long Settled Funding: {self.long_settled_funding}
    Short Settled Funding: {self.short_settled_funding}
    MNGO Accrued: {self.mngo_accrued}
    OpenOrders:
        {open_orders}
»"""
