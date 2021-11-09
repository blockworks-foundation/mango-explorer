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

from ..account import Account
from ..cache import Cache
from ..group import Group
from ..instrumentvalue import InstrumentValue
from ..openorders import OpenOrders

from .collateralcalculator import CollateralCalculator


class SerumCollateralCalculator(CollateralCalculator):
    def __init__(self) -> None:
        super().__init__()

    def calculate(self, account: Account, all_open_orders: typing.Dict[str, OpenOrders], group: Group, cache: Cache) -> InstrumentValue:
        raise NotImplementedError("SerumCollateralCalculator.calculate() is not implemented.")
