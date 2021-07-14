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


from solana.publickey import PublicKey

from .market import AddressableMarket, InventorySource
from .token import Token


# # 🥭 PerpsMarket class
#
# This class encapsulates our knowledge of a Mango perps market.
#


class PerpsMarket(AddressableMarket):
    def __init__(self, base: Token, quote: Token, address: PublicKey):
        super().__init__(InventorySource.ACCOUNT, base, quote, address)

    @property
    def symbol(self) -> str:
        return f"{self.base.symbol}-PERP"

    def __str__(self) -> str:
        return f"« 𝙿𝚎𝚛𝚙𝚜𝙼𝚊𝚛𝚔𝚎𝚝 {self.symbol} [{self.address}] »"
