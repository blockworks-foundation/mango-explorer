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

from .context import Context
from .lotsizeconverter import LotSizeConverter
from .market import Market, InventorySource
from .orders import Order
from .token import Token


# # 🥭 LoadedMarket class
#
# This class describes a crypto market. It *must* have an address, a base token and a quote token.
#
class LoadedMarket(Market):
    def __init__(self, program_address: PublicKey, address: PublicKey, inventory_source: InventorySource, base: Token, quote: Token, lot_size_converter: LotSizeConverter):
        super().__init__(program_address, address, inventory_source, base, quote, lot_size_converter)

    def orders(self, context: Context) -> typing.Sequence[Order]:
        raise NotImplementedError("LoadedMarket.orders() is not implemented on the base type.")
