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
import mango
import typing

from decimal import Decimal


# # 🥭 ModelState class
#
# Provides simple access to the latest state of market and account data.
#
class ModelState:
    def __init__(self, market: mango.Market,
                 group_watcher: mango.Watcher[mango.Group],
                 account_watcher: mango.Watcher[mango.Account],
                 price_watcher: mango.Watcher[mango.Price],
                 placed_orders_container_watcher: mango.Watcher[mango.PlacedOrdersContainer],
                 inventory_watcher: mango.Watcher[mango.Inventory],
                 bids: mango.Watcher[typing.Sequence[mango.Order]],
                 asks: mango.Watcher[typing.Sequence[mango.Order]]
                 ):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.market: mango.Market = market
        self.group_watcher: mango.Watcher[mango.Group] = group_watcher
        self.account_watcher: mango.Watcher[mango.Account] = account_watcher
        self.price_watcher: mango.Watcher[mango.Price] = price_watcher
        self.placed_orders_container_watcher: mango.Watcher[
            mango.PlacedOrdersContainer] = placed_orders_container_watcher
        self.inventory_watcher: mango.Watcher[
            mango.Inventory] = inventory_watcher
        self.bids_watcher: mango.Watcher[typing.Sequence[mango.Order]] = bids
        self.asks_watcher: mango.Watcher[typing.Sequence[mango.Order]] = asks

    @property
    def group(self) -> mango.Group:
        return self.group_watcher.latest

    @property
    def account(self) -> mango.Account:
        return self.account_watcher.latest

    @property
    def price(self) -> mango.Price:
        return self.price_watcher.latest

    @property
    def placed_orders_container(self) -> mango.PlacedOrdersContainer:
        return self.placed_orders_container_watcher.latest

    @property
    def inventory(self) -> mango.Inventory:
        return self.inventory_watcher.latest

    @property
    def bids(self) -> typing.Sequence[mango.Order]:
        return self.bids_watcher.latest

    @property
    def asks(self) -> typing.Sequence[mango.Order]:
        return self.asks_watcher.latest

    @property
    def top_bid(self) -> typing.Union[mango.Order, None]:
        if self.bids_watcher.latest:
            return self.bids_watcher.latest[0]
        else:
            return None

    @property
    def top_ask(self) -> typing.Union[mango.Order, None]:
        if self.asks_watcher.latest:
            return self.asks_watcher.latest[0]
        else:
            return None

    @property
    def spread(self) -> Decimal:
        top_ask = self.top_ask
        top_bid = self.top_bid
        if top_ask is None or top_bid is None:
            return Decimal(0)
        else:
            return self.top_ask.price - self.top_bid.price

    @property
    def existing_orders(self) -> typing.Sequence[mango.PlacedOrder]:
        return self.placed_orders_container_watcher.latest.placed_orders

    def __str__(self) -> str:
        return f"""« 𝙼𝚘𝚍𝚎𝚕𝚂𝚝𝚊𝚝𝚎 for market '{self.market.symbol}'
    Group: {self.group_watcher.latest.address}
    Account: {self.account_watcher.latest.address}
    Price: {self.price_watcher.latest}
    Inventory: {self.inventory_watcher.latest}
    Existing Order Count: {len(self.placed_orders_container_watcher.latest.placed_orders)}
    Bid Count: {len(self.bids_watcher.latest)}
    Ask Count: {len(self.bids_watcher.latest)}
»"""

    def __repr__(self) -> str:
        return f"{self}"
