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

from .openorders import PlacedOrder


# # 🥭 PerpOpenOrders class
#
class PerpOpenOrders:
    def __init__(self, placed_orders: typing.Sequence[PlacedOrder]):
        self.placed_orders: typing.Sequence[PlacedOrder] = placed_orders

    @property
    def empty(self) -> bool:
        return len(self.placed_orders) == 0

    def __str__(self) -> str:
        placed_orders = "\n        ".join(map(str, self.placed_orders)) or "None"

        return f"""« 𝙿𝚎𝚛𝚙𝙾𝚙𝚎𝚗𝙾𝚛𝚍𝚎𝚛𝚜
    Orders:
        {placed_orders}
»"""
