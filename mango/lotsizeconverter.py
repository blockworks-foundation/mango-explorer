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

from .token import Token


# # 🥭 LotSizeConverter class
#
class LotSizeConverter():
    def __init__(self, base: Token, base_lot_size: Decimal, quote: Token, quote_lot_size: Decimal):
        self.base: Token = base
        self.base_lot_size: Decimal = base_lot_size
        self.quote: Token = quote
        self.quote_lot_size: Decimal = quote_lot_size

    @property
    def min_order_size(self) -> Decimal:
        return self.base_size_lots_to_number(Decimal(1))

    @property
    def tick_size(self) -> Decimal:
        return self.price_lots_to_number(Decimal(1))

    def price_lots_to_number(self, price_lots: Decimal) -> Decimal:
        adjusted = 10 ** (self.base.decimals - self.quote.decimals)
        lots_to_native = self.quote_lot_size / self.base_lot_size
        return (price_lots * lots_to_native) * adjusted

    def price_number_to_lots(self, price: Decimal) -> int:
        base_factor: Decimal = 10 ** self.base.decimals
        quote_factor: Decimal = 10 ** self.quote.decimals
        return round((price * quote_factor * self.base_lot_size) / (base_factor * self.quote_lot_size))

    def base_size_lots_to_number(self, size_lots: Decimal) -> Decimal:
        size: int = round(size_lots)
        base_factor: Decimal = 10 ** self.base.decimals
        return Decimal(size * self.base_lot_size) / base_factor

    def base_size_number_to_lots(self, size: Decimal) -> int:
        base_factor: Decimal = 10 ** self.base.decimals
        return int(round(size * base_factor) / self.base_lot_size)

    def quote_size_lots_to_number(self, size_lots: Decimal) -> Decimal:
        size: int = round(size_lots)
        quote_factor: Decimal = 10 ** self.quote.decimals
        return Decimal(size * self.quote_lot_size) / quote_factor

    def quote_lots_to_number(self, size_lots: Decimal) -> Decimal:
        quote_factor: Decimal = 10 ** self.quote.decimals
        return Decimal(size_lots * self.quote_lot_size) / quote_factor

    def quote_size_number_to_lots(self, size: Decimal) -> int:
        quote_factor: Decimal = 10 ** self.quote.decimals
        return int(round(size * quote_factor) / self.quote_lot_size)

    def round_base(self, quantity: Decimal) -> Decimal:
        lots: int = self.base_size_number_to_lots(quantity)
        return self.base_size_lots_to_number(Decimal(lots))

    def round_quote(self, price: Decimal) -> Decimal:
        lots: int = self.quote_size_number_to_lots(price)
        return self.quote_size_lots_to_number(Decimal(lots))

    def __str__(self) -> str:
        return f"« 𝙻𝚘𝚝𝚂𝚒𝚣𝚎𝙲𝚘𝚗𝚟𝚎𝚛𝚝𝚎𝚛 {self.base.symbol}/{self.quote.symbol} [base lot size: {self.base_lot_size} ({self.base.decimals} decimals), quote lot size: {self.quote_lot_size} ({self.quote.decimals} decimals)] »"

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 NullLotSizeConverter class
#
class NullLotSizeConverter(LotSizeConverter):
    def __init__(self):
        super().__init__(None, Decimal(1), None, Decimal(1))

    def price_lots_to_number(self, price_lots: Decimal) -> Decimal:
        return price_lots

    def price_number_to_lots(self, price: Decimal) -> int:
        return round(price)

    def base_size_lots_to_number(self, size_lots: Decimal) -> Decimal:
        return size_lots

    def base_size_number_to_lots(self, size: Decimal) -> int:
        return round(size)

    def quote_size_lots_to_number(self, size_lots: Decimal) -> Decimal:
        return size_lots

    def quote_size_number_to_lots(self, size: Decimal) -> int:
        return round(size)

    def __str__(self) -> str:
        return "« 𝙽𝚞𝚕𝚕𝙻𝚘𝚝𝚂𝚒𝚣𝚎𝙲𝚘𝚗𝚟𝚎𝚛𝚝𝚎𝚛 »"


# # 🥭 RaisingLotSizeConverter class
#
class RaisingLotSizeConverter(LotSizeConverter):
    def __init__(self):
        super().__init__(None, Decimal(-1), None, Decimal(-1))

    def price_lots_to_number(self, price_lots: Decimal) -> Decimal:
        raise NotImplementedError(
            "RaisingLotSizeConverter.price_lots_to_number() is not implemented. RaisingLotSizeConverter is a stub used where no LotSizeConverter members should be called.")

    def price_number_to_lots(self, price: Decimal) -> int:
        raise NotImplementedError(
            "RaisingLotSizeConverter.price_number_to_lots() is not implemented. RaisingLotSizeConverter is a stub used where no LotSizeConverter members should be called.")

    def base_size_lots_to_number(self, size_lots: Decimal) -> Decimal:
        raise NotImplementedError(
            "RaisingLotSizeConverter.base_size_lots_to_number() is not implemented. RaisingLotSizeConverter is a stub used where no LotSizeConverter members should be called.")

    def base_size_number_to_lots(self, size: Decimal) -> int:
        raise NotImplementedError(
            "RaisingLotSizeConverter.base_size_number_to_lots() is not implemented. RaisingLotSizeConverter is a stub used where no LotSizeConverter members should be called.")

    def quote_size_lots_to_number(self, size_lots: Decimal) -> Decimal:
        raise NotImplementedError(
            "RaisingLotSizeConverter.quote_size_lots_to_number() is not implemented. RaisingLotSizeConverter is a stub used where no LotSizeConverter members should be called.")

    def quote_size_number_to_lots(self, size: Decimal) -> int:
        raise NotImplementedError(
            "RaisingLotSizeConverter.quote_size_number_to_lots() is not implemented. RaisingLotSizeConverter is a stub used where no LotSizeConverter members should be called.")

    def __str__(self) -> str:
        return "« 𝚁𝚊𝚒𝚜𝚒𝚗𝚐𝙻𝚘𝚝𝚂𝚒𝚣𝚎𝙲𝚘𝚗𝚟𝚎𝚛𝚝𝚎𝚛 »"
