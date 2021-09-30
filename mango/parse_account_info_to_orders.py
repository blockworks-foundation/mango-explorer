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

from pyserum.market import Market as PySerumMarket
from pyserum.market.orderbook import OrderBook as PySerumOrderBook

from .accountinfo import AccountInfo
from .orders import Order


# # 🥭 parse_account_info_to_orders function
#
# This just parses an `AccountInfo` for a Serum orderbook side into a list of `Order`s.
#
# It's here on its own because putting it in orders.py caused a circular reference and I couldn't think
# of a better place.
#
def parse_account_info_to_orders(account_info: AccountInfo, pyserum_market: PySerumMarket) -> typing.Sequence[Order]:
    serum_orderbook_side = PySerumOrderBook.from_bytes(pyserum_market.state, account_info.data)
    orders: typing.List[Order] = list(map(Order.from_serum_order, serum_orderbook_side.orders()))
    if serum_orderbook_side._is_bids:
        orders.reverse()

    return orders
