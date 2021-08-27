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

from .account import Account
from .group import Group
from .market import InventorySource, Market
from .perpmarket import PerpMarket
from .tokenvalue import TokenValue
from .watcher import Watcher


# # 🥭 Inventory class
#
# This class details inventory of a crypto account for a market.
#

class Inventory:
    def __init__(self, inventory_source: InventorySource, liquidity_incentives: TokenValue, base: TokenValue, quote: TokenValue):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.inventory_source: InventorySource = inventory_source
        self.liquidity_incentives: TokenValue = liquidity_incentives
        self.base: TokenValue = base
        self.quote: TokenValue = quote

    @property
    def symbol(self) -> str:
        return f"{self.base.token.symbol}/{self.quote.token.symbol}"

    def __str__(self) -> str:
        liquidity_incentives: str = ""
        if self.liquidity_incentives.value > 0:
            liquidity_incentives = f" {self.liquidity_incentives}"
        return f"« 𝙸𝚗𝚟𝚎𝚗𝚝𝚘𝚛𝚢 {self.symbol}{liquidity_incentives} [{self.base} / {self.quote}] »"

    def __repr__(self) -> str:
        return f"{self}"


class SpotInventoryAccountWatcher:
    def __init__(self, market: Market, account_watcher: Watcher[Account]):
        self.account_watcher: Watcher[Account] = account_watcher
        account: Account = account_watcher.latest
        base_value = TokenValue.find_by_symbol(account.net_assets, market.base.symbol)
        self.base_index: int = account.net_assets.index(base_value)
        quote_value = TokenValue.find_by_symbol(account.net_assets, market.quote.symbol)
        self.quote_index: int = account.net_assets.index(quote_value)

    @property
    def latest(self) -> Inventory:
        account: Account = self.account_watcher.latest

        # Spot markets don't accrue MNGO liquidity incentives
        mngo = account.group.find_token_info_by_symbol("MNGO").token
        mngo_accrued: TokenValue = TokenValue(mngo, Decimal(0))

        base_value = account.net_assets[self.base_index]
        if base_value is None:
            raise Exception(
                f"Could not find net assets in account {account.address} at index {self.base_index}.")
        quote_value = account.net_assets[self.quote_index]
        if quote_value is None:
            raise Exception(
                f"Could not find net assets in account {account.address} at index {self.quote_index}.")

        return Inventory(InventorySource.ACCOUNT, mngo_accrued, base_value, quote_value)


class PerpInventoryAccountWatcher:
    def __init__(self, market: PerpMarket, account_watcher: Watcher[Account], group: Group):
        self.market: PerpMarket = market
        self.account_watcher: Watcher[Account] = account_watcher
        self.perp_account_index: int = group.find_perp_market_index(market.address)
        account: Account = account_watcher.latest
        quote_value = TokenValue.find_by_symbol(account.net_assets, market.quote.symbol)
        self.quote_index: int = account.net_assets.index(quote_value)

    @property
    def latest(self) -> Inventory:
        perp_account = self.account_watcher.latest.perp_accounts[self.perp_account_index]
        if perp_account is None:
            raise Exception(
                f"Could not find perp account for {self.market.symbol} in account {self.account_watcher.latest.address} at index {self.perp_account_index}.")
        base_lots = perp_account.base_position
        base_value = self.market.lot_size_converter.quantity_lots_to_value(base_lots)
        base_token_value = TokenValue(self.market.base, base_value)
        quote_token_value = self.account_watcher.latest.net_assets[self.quote_index]
        if quote_token_value is None:
            raise Exception(
                f"Could not find net assets in account {self.account_watcher.latest.address} at index {self.quote_index}.")
        return Inventory(InventorySource.ACCOUNT, perp_account.mngo_accrued, base_token_value, quote_token_value)
