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


import enum
import logging
import typing

from decimal import Decimal

from .account import Account
from .group import Group
from .instrumentvalue import InstrumentValue


# # 🥭 LiquidatableState flag enum
#
# A margin account may have a combination of these flag values.
#

class LiquidatableState(enum.Flag):
    UNSET = 0
    RIPE = enum.auto()
    BEING_LIQUIDATED = enum.auto()
    LIQUIDATABLE = enum.auto()
    ABOVE_WATER = enum.auto()
    WORTHWHILE = enum.auto()


# # 🥭 LiquidatableReport class
#

class LiquidatableReport:
    def __init__(self, group: Group, prices: typing.Sequence[InstrumentValue], account: Account, state: LiquidatableState, worthwhile_threshold: Decimal) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.group: Group = group
        self.prices: typing.Sequence[InstrumentValue] = prices
        self.account: Account = account
        self.state: LiquidatableState = state
        self.worthwhile_threshold: Decimal = worthwhile_threshold

    @staticmethod
    def build(group: Group, prices: typing.Sequence[InstrumentValue], account: Account, worthwhile_threshold: Decimal) -> "LiquidatableReport":
        return LiquidatableReport(group, prices, account, LiquidatableState.UNSET, worthwhile_threshold)
