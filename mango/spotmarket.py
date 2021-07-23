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
from pyserum.market.types import Order as SerumOrder
from solana.publickey import PublicKey

from .accountinfo import AccountInfo
from .context import Context
from .market import AddressableMarket, InventorySource
from .serumeventqueue import SerumEvent, SerumEventQueue
from .token import Token


# # 🥭 SpotMarket class
#
# This class encapsulates our knowledge of a Serum spot market.
#


class SpotMarket(AddressableMarket):
    def __init__(self, base: Token, quote: Token, address: PublicKey, group_address: PublicKey):
        super().__init__(InventorySource.ACCOUNT, base, quote, address)
        self.group_address: PublicKey = group_address
        self.underlying_serum_market: typing.Optional[PySerumMarket] = None
        self.loaded: bool = False

    def load(self, context: Context) -> None:
        self.underlying_serum_market = PySerumMarket.load(context.client, self.address, context.dex_program_id)
        self.loaded = True

    def ensure_loaded(self, context: Context) -> None:
        if not self.loaded:
            self.load(context)

    def unprocessed_events(self, context: Context) -> typing.Sequence[SerumEvent]:
        if self.underlying_serum_market is None:
            raise Exception(f"SpotMarket {self.symbol} has not been loaded.")

        event_queue: SerumEventQueue = SerumEventQueue.load(context, self.underlying_serum_market.state.event_queue())
        return event_queue.unprocessed_events()

    def orders(self, context: Context) -> typing.Sequence[SerumOrder]:
        if self.underlying_serum_market is None:
            raise Exception(f"SpotMarket {self.symbol} has not been loaded.")

        raw_market = self.underlying_serum_market
        [bids_info, asks_info] = AccountInfo.load_multiple(
            context, [raw_market.state.bids(), raw_market.state.asks()])
        bids_orderbook = SerumOrderBook.from_bytes(raw_market.state, bids_info.data)
        asks_orderbook = SerumOrderBook.from_bytes(raw_market.state, asks_info.data)

        return list(itertools.chain(bids_orderbook.orders(), asks_orderbook.orders()))

    def __str__(self) -> str:
        return f"« 𝚂𝚙𝚘𝚝𝙼𝚊𝚛𝚔𝚎𝚝 {self.symbol} [{self.address}] »"
