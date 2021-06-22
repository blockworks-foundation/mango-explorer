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

from .balancesheet import BalanceSheet
from .group import Group
from .marginaccount import MarginAccount
from .tokenvalue import TokenValue


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
    def __init__(self, group: Group, prices: typing.List[TokenValue], margin_account: MarginAccount, balance_sheet: BalanceSheet, balances: typing.List[TokenValue], state: LiquidatableState, worthwhile_threshold: Decimal):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.group: Group = group
        self.prices: typing.List[TokenValue] = prices
        self.margin_account: MarginAccount = margin_account
        self.balance_sheet: BalanceSheet = balance_sheet
        self.balances: typing.List[TokenValue] = balances
        self.state: LiquidatableState = state
        self.worthwhile_threshold: Decimal = worthwhile_threshold

    @staticmethod
    def build(group: Group, prices: typing.List[TokenValue], margin_account: MarginAccount, worthwhile_threshold: Decimal) -> "LiquidatableReport":
        balance_sheet = margin_account.get_balance_sheet_totals(group, prices)
        balances = margin_account.get_intrinsic_balances(group)

        state = LiquidatableState.UNSET

        if balance_sheet.collateral_ratio != Decimal(0):
            if balance_sheet.collateral_ratio <= group.init_coll_ratio:
                state |= LiquidatableState.RIPE

            if balance_sheet.collateral_ratio <= group.maint_coll_ratio:
                state |= LiquidatableState.LIQUIDATABLE

            if balance_sheet.collateral_ratio > Decimal(1):
                state |= LiquidatableState.ABOVE_WATER

            if balance_sheet.assets - balance_sheet.liabilities > worthwhile_threshold:
                state |= LiquidatableState.WORTHWHILE

        # If a liquidation is ongoing, their account may be above the `maint_coll_ratio` but still
        # be liquidatable until it reaches `init_coll_ratio`.
        if margin_account.being_liquidated:
            state |= LiquidatableState.BEING_LIQUIDATED
            state |= LiquidatableState.LIQUIDATABLE

        return LiquidatableReport(group, prices, margin_account, balance_sheet, balances, state, worthwhile_threshold)
