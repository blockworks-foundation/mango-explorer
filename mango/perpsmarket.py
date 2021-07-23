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

from solana.publickey import PublicKey

from .accountinfo import AccountInfo
from .context import Context
from .market import AddressableMarket, InventorySource
from .orderbookside import OrderBookSide
from .orders import Order
from .perpeventqueue import PerpEvent, PerpEventQueue
from .perpmarket import PerpMarket
from .token import Token


# # 🥭 PerpsMarket class
#
# This class encapsulates our knowledge of a Mango perps market.
#

class PerpsMarket(AddressableMarket):
    def __init__(self, base: Token, quote: Token, address: PublicKey, group_address: PublicKey):
        super().__init__(InventorySource.ACCOUNT, base, quote, address)
        self.group_address: PublicKey = group_address
        self.underlying_perp_market: typing.Optional[PerpMarket] = None
        self.loaded: bool = False

    def load(self, context: Context) -> None:
        self.underlying_perp_market = PerpMarket.load_with_group(context, self.address)
        self.loaded = True

    def ensure_loaded(self, context: Context) -> None:
        if not self.loaded:
            self.load(context)

    @property
    def symbol(self) -> str:
        return f"{self.base.symbol}-PERP"

    def unprocessed_events(self, context: Context) -> typing.Sequence[PerpEvent]:
        if self.underlying_perp_market is None:
            raise Exception(f"PerpsMarket {self.symbol} has not been loaded.")

        event_queue: PerpEventQueue = PerpEventQueue.load(context, self.underlying_perp_market.event_queue)
        return event_queue.unprocessed_events()

    def accounts_to_crank(self, context: Context, additional_account_to_crank: typing.Optional[PublicKey]) -> typing.Sequence[PublicKey]:
        accounts_to_crank: typing.List[PublicKey] = []
        for event_to_crank in self.unprocessed_events(context):
            accounts_to_crank += event_to_crank.accounts_to_crank

        if additional_account_to_crank is not None:
            accounts_to_crank += [additional_account_to_crank]

        seen = []
        distinct = []
        for account in accounts_to_crank:
            account_str = account.to_base58()
            if account_str not in seen:
                distinct += [account]
                seen += [account_str]
        distinct.sort(key=lambda address: address._key or [0])
        return distinct

    def orders(self, context: Context) -> typing.Sequence[Order]:
        if self.underlying_perp_market is None:
            raise Exception(f"PerpsMarket {self.symbol} has not been loaded.")

        bids_address: PublicKey = self.underlying_perp_market.bids
        asks_address: PublicKey = self.underlying_perp_market.asks
        [bids, asks] = AccountInfo.load_multiple(context, [bids_address, asks_address])
        bid_side = OrderBookSide.parse(context, bids, self.underlying_perp_market)
        ask_side = OrderBookSide.parse(context, asks, self.underlying_perp_market)
        return [*bid_side.orders(), *ask_side.orders()]

    def __str__(self) -> str:
        return f"« 𝙿𝚎𝚛𝚙𝚜𝙼𝚊𝚛𝚔𝚎𝚝 {self.symbol} [{self.address}] »"
