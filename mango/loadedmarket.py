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
from .lotsizeconverter import LotSizeConverter
from .market import Market, InventorySource
from .orders import Order, OrderBook
from .token import Instrument, Token


# # 🥭 LoadedMarket class
#
# This class describes a crypto market. It *must* have an address, a base token and a quote token.
#
class LoadedMarket(Market):
    def __init__(self, program_address: PublicKey, address: PublicKey, inventory_source: InventorySource, base: Instrument, quote: Token, lot_size_converter: LotSizeConverter) -> None:
        super().__init__(program_address, address, inventory_source, base, quote, lot_size_converter)

    @property
    def bids_address(self) -> PublicKey:
        raise NotImplementedError("LoadedMarket.bids_address() is not implemented on the base type.")

    @property
    def asks_address(self) -> PublicKey:
        raise NotImplementedError("LoadedMarket.asks_address() is not implemented on the base type.")

    def parse_account_info_to_orders(self, account_info: AccountInfo) -> typing.Sequence[Order]:
        raise NotImplementedError("LoadedMarket.parse_account_info_to_orders() is not implemented on the base type.")

    def parse_account_infos_to_orderbook(self, bids_account_info: AccountInfo, asks_account_info: AccountInfo) -> OrderBook:
        bids_orderbook = self.parse_account_info_to_orders(bids_account_info)
        asks_orderbook = self.parse_account_info_to_orders(asks_account_info)
        return OrderBook(self.symbol, self.lot_size_converter, bids_orderbook, asks_orderbook)

    def fetch_orderbook(self, context: Context) -> OrderBook:
        [bids_info, asks_info] = AccountInfo.load_multiple(context, [self.bids_address, self.asks_address])
        return self.parse_account_infos_to_orderbook(bids_info, asks_info)
