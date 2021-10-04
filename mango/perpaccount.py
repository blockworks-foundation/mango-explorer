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

from .cache import PerpMarketCache
from .lotsizeconverter import LotSizeConverter
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
                 open_orders: PerpOpenOrders, lot_size_converter: LotSizeConverter,
                 base_token_value: TokenValue, quote_position_raw: Decimal):
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
        self.lot_size_converter: LotSizeConverter = lot_size_converter
        self.base_token_value: TokenValue = base_token_value
        self.quote_position_raw: Decimal = quote_position_raw

    @staticmethod
    def from_layout(layout: typing.Any, base_token: Token, quote_token: Token, open_orders: PerpOpenOrders, lot_size_converter: LotSizeConverter, mngo_token: Token) -> "PerpAccount":
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

        base_position_raw = (base_position + taker_base) * lot_size_converter.base_lot_size
        base_token_value: TokenValue = TokenValue(base_token, base_token.shift_to_decimals(base_position_raw))

        quote_position_raw: Decimal = quote_token.shift_to_decimals(quote_position)

        return PerpAccount(base_position, quote_position, long_settled_funding, short_settled_funding,
                           bids_quantity, asks_quantity, taker_base, taker_quote, mngo_accrued, open_orders,
                           lot_size_converter, base_token_value, quote_position_raw)

    @property
    def empty(self) -> bool:
        if self.base_position == Decimal(0) and self.quote_position == Decimal(0) and self.long_settled_funding == Decimal(0) and self.short_settled_funding == Decimal(0) and self.mngo_accrued.value == Decimal(0) and self.open_orders.empty:
            return True
        return False

    def unsettled_funding(self, perp_market_cache: PerpMarketCache) -> Decimal:
        if self.base_position < 0:
            return self.base_position * (perp_market_cache.short_funding - self.short_settled_funding)
        else:
            return self.base_position * (perp_market_cache.long_funding - self.long_settled_funding)

    def asset_value(self, perp_market_cache: PerpMarketCache, price: Decimal) -> Decimal:
        value: Decimal = Decimal(0)
        if self.base_position > 0:
            value = self.base_position * self.lot_size_converter.base_lot_size * price

        quote_position: Decimal = self.quote_position
        if self.base_position > 0:
            quote_position -= (perp_market_cache.long_funding - self.long_settled_funding) * self.base_position
        elif self.base_position < 0:
            quote_position -= (perp_market_cache.short_funding - self.short_settled_funding) * self.base_position

        if quote_position > 0:
            value += quote_position

        return self.lot_size_converter.quote.shift_to_decimals(value)

    def liability_value(self, perp_market_cache: PerpMarketCache, price: Decimal) -> Decimal:
        value: Decimal = Decimal(0)
        if self.base_position < 0:
            value = self.base_position * self.lot_size_converter.base_lot_size * price

        quote_position: Decimal = self.quote_position
        if self.base_position > 0:
            quote_position -= (perp_market_cache.long_funding - self.long_settled_funding) * self.base_position
        elif self.base_position < 0:
            quote_position -= (perp_market_cache.short_funding - self.short_settled_funding) * self.base_position

        if quote_position < 0:
            value += quote_position

        return self.lot_size_converter.quote.shift_to_decimals(-value)

    def __str__(self) -> str:
        if self.empty:
            return "« 𝙿𝚎𝚛𝚙𝙰𝚌𝚌𝚘𝚞𝚗𝚝 (empty) »"
        open_orders = f"{self.open_orders}".replace("\n", "\n        ")
        return f"""« 𝙿𝚎𝚛𝚙𝙰𝚌𝚌𝚘𝚞𝚗𝚝
    Base Position: {self.base_token_value}
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
