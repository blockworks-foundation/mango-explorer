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

from datetime import datetime
from decimal import Decimal
from solana.publickey import PublicKey

from .accountinfo import AccountInfo
from .addressableaccount import AddressableAccount
from .context import Context
from .layouts import layouts
from .metadata import Metadata
from .version import Version


# # 🥭 NodeBank class
#
# `NodeBank` stores details of deposits/borrows and vault.
#


class PriceCache:
    def __init__(self, price: Decimal, last_update: datetime):
        self.price: Decimal = price
        self.last_update: datetime = last_update

    @staticmethod
    def from_layout(layout: typing.Any) -> typing.Optional["PriceCache"]:
        if layout.last_update.timestamp() == 0:
            return None
        return PriceCache(layout.price, layout.last_update)

    def __str__(self) -> str:
        return f"« 𝙿𝚛𝚒𝚌𝚎𝙲𝚊𝚌𝚑𝚎 [{self.last_update}] {self.price:,.8f} »"

    def __repr__(self) -> str:
        return f"{self}"


class RootBankCache:
    def __init__(self, deposit_index: Decimal, borrow_index: Decimal, last_update: datetime):
        self.deposit_index: Decimal = deposit_index
        self.borrow_index: Decimal = borrow_index
        self.last_update: datetime = last_update

    @staticmethod
    def from_layout(layout: typing.Any) -> typing.Optional["RootBankCache"]:
        if layout.last_update.timestamp() == 0:
            return None
        return RootBankCache(layout.deposit_index, layout.borrow_index, layout.last_update)

    def __str__(self) -> str:
        return f"« 𝚁𝚘𝚘𝚝𝙱𝚊𝚗𝚔𝙲𝚊𝚌𝚑𝚎 [{self.last_update}] {self.deposit_index:,.8f} / {self.borrow_index:,.8f} »"

    def __repr__(self) -> str:
        return f"{self}"


class PerpMarketCache:
    def __init__(self, long_funding: Decimal, short_funding: Decimal, last_update: datetime):
        self.long_funding: Decimal = long_funding
        self.short_funding: Decimal = short_funding
        self.last_update: datetime = last_update

    @staticmethod
    def from_layout(layout: typing.Any) -> typing.Optional["PerpMarketCache"]:
        if layout.last_update.timestamp() == 0:
            return None
        return PerpMarketCache(layout.long_funding, layout.short_funding, layout.last_update)

    def __str__(self) -> str:
        return f"« 𝙿𝚎𝚛𝚙𝙼𝚊𝚛𝚔𝚎𝚝𝙲𝚊𝚌𝚑𝚎 [{self.last_update}] {self.long_funding:,.8f} / {self.short_funding:,.8f} »"

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 Cache class
#
# `Cache` stores cache details of prices, root banks and perp markets.
#

class Cache(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version, meta_data: Metadata,
                 price_cache: typing.Sequence[typing.Optional[PriceCache]],
                 root_bank_cache: typing.Sequence[typing.Optional[RootBankCache]],
                 perp_market_cache: typing.Sequence[typing.Optional[PerpMarketCache]]):
        super().__init__(account_info)
        self.version: Version = version

        self.meta_data: Metadata = meta_data
        self.price_cache: typing.Sequence[typing.Optional[PriceCache]] = price_cache
        self.root_bank_cache: typing.Sequence[typing.Optional[RootBankCache]] = root_bank_cache
        self.perp_market_cache: typing.Sequence[typing.Optional[PerpMarketCache]] = perp_market_cache

    @staticmethod
    def from_layout(layout: typing.Any, account_info: AccountInfo, version: Version) -> "Cache":
        meta_data: Metadata = Metadata.from_layout(layout.meta_data)
        price_cache: typing.Sequence[typing.Optional[PriceCache]] = list(
            map(PriceCache.from_layout, layout.price_cache))
        root_bank_cache: typing.Sequence[typing.Optional[RootBankCache]] = list(
            map(RootBankCache.from_layout, layout.root_bank_cache))
        perp_market_cache: typing.Sequence[typing.Optional[PerpMarketCache]] = list(
            map(PerpMarketCache.from_layout, layout.perp_market_cache))

        return Cache(account_info, version, meta_data, price_cache, root_bank_cache, perp_market_cache)

    @staticmethod
    def parse(account_info: AccountInfo) -> "Cache":
        data = account_info.data
        if len(data) != layouts.CACHE.sizeof():
            raise Exception(
                f"Cache data length ({len(data)}) does not match expected size ({layouts.CACHE.sizeof()})")

        layout = layouts.CACHE.parse(data)
        return Cache.from_layout(layout, account_info, Version.V1)

    @staticmethod
    def load(context: Context, address: PublicKey) -> "Cache":
        account_info = AccountInfo.load(context, address)
        if account_info is None:
            raise Exception(f"Cache account not found at address '{address}'")
        return Cache.parse(account_info)

    def __str__(self) -> str:
        def _render_list(items, stub):
            rendered = []
            for index, item in enumerate(items):
                rendered += [f"{index}: {(item or stub)}".replace("\n", "\n            ")]
            return rendered
        prices = "\n        ".join(_render_list(self.price_cache, "« No 𝙿𝚛𝚒𝚌𝚎𝙲𝚊𝚌𝚑𝚎 »"))
        root_banks = "\n        ".join(_render_list(self.root_bank_cache, "« No 𝚁𝚘𝚘𝚝𝙱𝚊𝚗𝚔𝙲𝚊𝚌𝚑𝚎 »"))
        perp_markets = "\n        ".join(_render_list(self.perp_market_cache, "« No 𝙿𝚎𝚛𝚙𝙼𝚊𝚛𝚔𝚎𝚝𝙲𝚊𝚌𝚑𝚎 »"))
        return f"""« 𝙲𝚊𝚌𝚑𝚎 [{self.version}] {self.address}
    {self.meta_data}
    Prices:
        {prices}
    Root Banks:
        {root_banks}
    Perp Markets:
        {perp_markets}
»"""

    def __repr__(self) -> str:
        return f"{self}"
