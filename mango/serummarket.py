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

import itertools
import typing

from pyserum.market import Market as PySerumMarket
from pyserum.market.orderbook import OrderBook as SerumOrderBook
from solana.publickey import PublicKey

from .accountinfo import AccountInfo
from .context import Context
from .market import Market, InventorySource
from .orders import Order
from .serumeventqueue import SerumEvent, SerumEventQueue
from .token import Token


# # 🥭 SerumMarket class
#
# This class encapsulates our knowledge of a Serum spot market.
#


class SerumMarket(Market):
    def __init__(self, address: PublicKey, base: Token, quote: Token, underlying_serum_market: PySerumMarket):
        super().__init__(address, InventorySource.SPL_TOKENS, base, quote)
        self.underlying_serum_market: PySerumMarket = underlying_serum_market

    def unprocessed_events(self, context: Context) -> typing.Sequence[SerumEvent]:
        event_queue: SerumEventQueue = SerumEventQueue.load(context, self.underlying_serum_market.state.event_queue())
        return event_queue.unprocessed_events

    def orders(self, context: Context) -> typing.Sequence[Order]:
        raw_market = self.underlying_serum_market
        [bids_info, asks_info] = AccountInfo.load_multiple(
            context, [raw_market.state.bids(), raw_market.state.asks()])
        bids_orderbook = SerumOrderBook.from_bytes(raw_market.state, bids_info.data)
        asks_orderbook = SerumOrderBook.from_bytes(raw_market.state, asks_info.data)

        return list(map(Order.from_serum_order, itertools.chain(bids_orderbook.orders(), asks_orderbook.orders())))

    def __str__(self) -> str:
        return f"« 𝚂𝚎𝚛𝚞𝚖𝙼𝚊𝚛𝚔𝚎𝚝 {self.symbol} [{self.address}] »"


# # 🥭 SerumMarketStub class
#
# This class holds information to load a `SerumMarket` object but doesn't automatically load it.
#


class SerumMarketStub(Market):
    def __init__(self, address: PublicKey, base: Token, quote: Token):
        super().__init__(address, InventorySource.SPL_TOKENS, base, quote)

    def load(self, context: Context) -> SerumMarket:
        underlying_serum_market: PySerumMarket = PySerumMarket.load(
            context.client, self.address, context.dex_program_id)
        return SerumMarket(self.address, self.base, self.quote, underlying_serum_market)

    def __str__(self) -> str:
        return f"« 𝚂𝚎𝚛𝚞𝚖𝙼𝚊𝚛𝚔𝚎𝚝𝚂𝚝𝚞𝚋 {self.symbol} [{self.address}] »"
