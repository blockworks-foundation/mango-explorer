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
import typing

from decimal import Decimal
from solana.publickey import PublicKey

from .account import Account
from .group import Group
from .inventory import Inventory
from .market import Market
from .oracle import Price
from .orders import Order
from .placedorder import PlacedOrdersContainer
from .watcher import Watcher


# # 🥭 ModelState class
#
# Provides simple access to the latest state of market and account data.
#
class ModelState:
    def __init__(self,
                 order_owner: PublicKey,
                 market: Market,
                 group_watcher: Watcher[Group],
                 account_watcher: Watcher[Account],
                 price_watcher: Watcher[Price],
                 placed_orders_container_watcher: Watcher[PlacedOrdersContainer],
                 inventory_watcher: Watcher[Inventory],
                 bids: Watcher[typing.Sequence[Order]],
                 asks: Watcher[typing.Sequence[Order]]
                 ):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.order_owner: PublicKey = order_owner
        self.market: Market = market
        self.group_watcher: Watcher[Group] = group_watcher
        self.account_watcher: Watcher[Account] = account_watcher
        self.price_watcher: Watcher[Price] = price_watcher
        self.placed_orders_container_watcher: Watcher[
            PlacedOrdersContainer] = placed_orders_container_watcher
        self.inventory_watcher: Watcher[Inventory] = inventory_watcher
        self.bids_watcher: Watcher[typing.Sequence[Order]] = bids
        self.asks_watcher: Watcher[typing.Sequence[Order]] = asks

        self.not_quoting: bool = False
        self.state: typing.Dict[str, typing.Any] = {}

    @property
    def group(self) -> Group:
        return self.group_watcher.latest

    @property
    def account(self) -> Account:
        return self.account_watcher.latest

    @property
    def price(self) -> Price:
        return self.price_watcher.latest

    @property
    def placed_orders_container(self) -> PlacedOrdersContainer:
        return self.placed_orders_container_watcher.latest

    @property
    def inventory(self) -> Inventory:
        return self.inventory_watcher.latest

    @property
    def bids(self) -> typing.Sequence[Order]:
        return self.bids_watcher.latest

    @property
    def asks(self) -> typing.Sequence[Order]:
        return self.asks_watcher.latest

    # The top bid is the highest price someone is willing to pay to BUY
    @property
    def top_bid(self) -> typing.Optional[Order]:
        if self.bids_watcher.latest and len(self.bids_watcher.latest) > 0:
            # Top-of-book is always at index 0 for us.
            return self.bids_watcher.latest[0]
        else:
            return None

    # The top ask is the lowest price someone is willing to pay to SELL
    @property
    def top_ask(self) -> typing.Optional[Order]:
        if self.asks_watcher.latest and len(self.asks_watcher.latest) > 0:
            # Top-of-book is always at index 0 for us.
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
            return top_ask.price - top_bid.price

    def current_orders(self) -> typing.Sequence[Order]:
        all_orders = [*self.bids_watcher.latest, *self.asks_watcher.latest]
        return list([o for o in all_orders if o.owner == self.order_owner])

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
