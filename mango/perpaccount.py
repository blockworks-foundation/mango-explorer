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
from .token import Token
from .tokenvalue import TokenValue


# # 🥭 PerpAccount class
#
# Perp accounts aren't directly addressable. They exist as a sub-object of a full Mango `Account` object.
#
class PerpAccount:
    def __init__(self, base_position: Decimal, quote_position: Decimal, long_settled_funding: Decimal,
                 short_settled_funding: Decimal, bids_quantity: Decimal, asks_quantity: Decimal,
                 taker_base: Decimal, taker_quote: Decimal, mngo_accrued: TokenValue,
                 open_orders: PerpOpenOrders):
        self.base_position: Decimal = base_position
        self.quote_position: Decimal = quote_position
        self.long_settled_funding: Decimal = long_settled_funding
        self.short_settled_funding: Decimal = short_settled_funding
        self.bids_quantity: Decimal = bids_quantity
        self.asks_quantity: Decimal = asks_quantity
        self.taker_base: Decimal = taker_base
        self.taker_quote: Decimal = taker_quote
        self.mngo_accrued: TokenValue = mngo_accrued
        self.open_orders: PerpOpenOrders = open_orders

    @staticmethod
    def from_layout(layout: layouts.PERP_ACCOUNT, open_orders: PerpOpenOrders, mngo_token: Token) -> "PerpAccount":
        base_position: Decimal = layout.base_position
        quote_position: Decimal = layout.quote_position
        long_settled_funding: Decimal = layout.long_settled_funding
        short_settled_funding: Decimal = layout.short_settled_funding
        bids_quantity: Decimal = layout.bids_quantity
        asks_quantity: Decimal = layout.asks_quantity
        taker_base: Decimal = layout.taker_base
        taker_quote: Decimal = layout.taker_quote
        mngo_accrued_raw: Decimal = layout.mngo_accrued
        mngo_accrued: TokenValue = TokenValue(mngo_token, mngo_token.shift_to_decimals(mngo_accrued_raw))

        return PerpAccount(base_position, quote_position, long_settled_funding, short_settled_funding,
                           bids_quantity, asks_quantity, taker_base, taker_quote, mngo_accrued, open_orders)

    def __str__(self) -> str:
        if self.base_position == Decimal(0) and self.quote_position == Decimal(0) and self.long_settled_funding == Decimal(0) and self.short_settled_funding == Decimal(0) and self.mngo_accrued.value == Decimal(0) and self.open_orders.empty:
            return "« 𝙿𝚎𝚛𝚙𝙰𝚌𝚌𝚘𝚞𝚗𝚝 (empty) »"
        open_orders = f"{self.open_orders}".replace("\n", "\n        ")
        return f"""« 𝙿𝚎𝚛𝚙𝙰𝚌𝚌𝚘𝚞𝚗𝚝
    Base Position: {self.base_position}
    Quote Position: {self.quote_position}
    Long Settled Funding: {self.long_settled_funding}
    Short Settled Funding: {self.short_settled_funding}
    Bids Quantity: {self.bids_quantity}
    Asks Quantity: {self.asks_quantity}
    Taker Base: {self.taker_base}
    Taker Quote: {self.taker_quote}
    MNGO Accrued: {self.mngo_accrued}
    OpenOrders:
        {open_orders}
»"""
