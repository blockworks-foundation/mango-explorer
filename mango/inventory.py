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

from .account import Account
from .context import Context
from .market import InventorySource, Market
from .tokenaccount import TokenAccount
from .tokenvalue import TokenValue
from .wallet import Wallet
from .watcher import Watcher


# # 🥭 Inventory class
#
# This class details inventory of a crypto account for a market.
#

class Inventory:
    def __init__(self, inventory_source: InventorySource, base: TokenValue, quote: TokenValue):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.inventory_source: InventorySource = inventory_source
        self.base: TokenValue = base
        self.quote: TokenValue = quote

    @property
    def symbol(self) -> str:
        return f"{self.base.token.symbol}/{self.quote.token.symbol}"

    def __str__(self) -> str:
        return f"« 𝙸𝚗𝚟𝚎𝚗𝚝𝚘𝚛𝚢 {self.symbol} »"

    def __repr__(self) -> str:
        return f"{self}"


def spl_token_inventory_loader(context: Context, wallet: Wallet, market: Market) -> Inventory:
    base_account = TokenAccount.fetch_largest_for_owner_and_token(
        context, wallet.address, market.base)
    if base_account is None:
        raise Exception(
            f"Could not find token account owned by {wallet.address} for base token {market.base}.")
    quote_account = TokenAccount.fetch_largest_for_owner_and_token(
        context, wallet.address, market.quote)
    if quote_account is None:
        raise Exception(
            f"Could not find token account owned by {wallet.address} for quote token {market.quote}.")
    return Inventory(InventorySource.SPL_TOKENS, base_account.value, quote_account.value)


def account_inventory_loader(market: Market, account: Account) -> Inventory:
    base_value = TokenValue.find_by_symbol(account.net_assets, market.base.symbol)
    if base_value is None:
        raise Exception(f"Could not find net assets in account {account.address} for base token {market.base}.")
    quote_value = TokenValue.find_by_symbol(account.net_assets, market.quote.symbol)
    if quote_value is None:
        raise Exception(f"Could not find net assets in account {account.address} for quote token {market.quote}.")
    return Inventory(InventorySource.ACCOUNT, base_value, quote_value)


class InventoryAccountWatcher:
    def __init__(self, market: Market, account_watcher: Watcher[Account]):
        self.account_watcher: Watcher[Account] = account_watcher
        account: Account = account_watcher.latest
        base_value = TokenValue.find_by_symbol(account.net_assets, market.base.symbol)
        self.base_index: int = account.net_assets.index(base_value)
        quote_value = TokenValue.find_by_symbol(account.net_assets, market.quote.symbol)
        self.quote_index: int = account.net_assets.index(quote_value)

    @property
    def latest(self) -> Inventory:
        base_value = self.account_watcher.latest.net_assets[self.base_index]
        if base_value is None:
            raise Exception(
                f"Could not find net assets in account {self.account_watcher.latest.address} at index {self.base_index}.")
        quote_value = self.account_watcher.latest.net_assets[self.quote_index]
        if quote_value is None:
            raise Exception(
                f"Could not find net assets in account {self.account_watcher.latest.address} at index {self.quote_index}.")
        return Inventory(InventorySource.ACCOUNT, base_value, quote_value)
