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
                 account_watcher: mango.LatestItemObserverSubscriber[mango.Account],
                 group_watcher: mango.LatestItemObserverSubscriber[mango.Group],
                 price_watcher: mango.LatestItemObserverSubscriber[mango.Price],
                 perp_market_watcher: typing.Optional[mango.LatestItemObserverSubscriber[mango.PerpMarket]],
                 spot_market_watcher: mango.LatestItemObserverSubscriber[mango.SpotMarket],
                 spot_open_orders_watcher: mango.LatestItemObserverSubscriber[mango.OpenOrders]
                 ):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.market: mango.Market = market
        self.account_watcher: mango.LatestItemObserverSubscriber[mango.Account] = account_watcher
        self.group_watcher: mango.LatestItemObserverSubscriber[mango.Group] = group_watcher
        self.price_watcher: mango.LatestItemObserverSubscriber[mango.Price] = price_watcher
        self.perp_market_watcher: typing.Optional[mango.LatestItemObserverSubscriber[mango.PerpMarket]
                                                  ] = perp_market_watcher
        self.spot_market_watcher: mango.LatestItemObserverSubscriber[mango.SpotMarket] = spot_market_watcher
        self.spot_open_orders_watcher: mango.LatestItemObserverSubscriber[mango.OpenOrders] = spot_open_orders_watcher

    @property
    def group(self) -> mango.Group:
        return self.group_watcher.latest

    @property
    def account(self) -> mango.Account:
        return self.account_watcher.latest

    @property
    def perp_market(self) -> typing.Optional[mango.PerpMarket]:
        if self.perp_market_watcher is None:
            return None
        return self.perp_market_watcher.latest

    @property
    def spot_market(self) -> mango.SpotMarket:
        return self.spot_market_watcher.latest

    @property
    def spot_open_orders(self) -> mango.OpenOrders:
        return self.spot_open_orders_watcher.latest

    @property
    def price(self) -> mango.Price:
        return self.price_watcher.latest

    @property
    def placed_order_ids(self) -> typing.Sequence[typing.Tuple[Decimal, Decimal]]:
        results: typing.List[typing.Tuple[Decimal, Decimal]] = []
        if self.spot_open_orders is not None:
            for index, order_id in enumerate(self.spot_open_orders.orders):
                results += [(order_id, self.spot_open_orders.client_ids[index])]
            return results
        if self.perp_market is not None:
            perp_account = self.account.perp_accounts[self.perp_market.market_index]
            for index, order_id in enumerate(perp_account.open_orders.orders):
                results += [(order_id, perp_account.open_orders.client_order_ids[index])]
            return results

        raise Exception("Could not get placed order and client IDs - not a Spot or Perp market.")

    def __str__(self) -> str:
        return f"""« 𝙼𝚘𝚍𝚎𝚕𝚂𝚝𝚊𝚝𝚎 for market '{self.market.symbol}' »"""

    def __repr__(self) -> str:
        return f"{self}"
