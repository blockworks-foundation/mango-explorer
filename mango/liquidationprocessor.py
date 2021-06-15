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


import logging
import time
import typing

from datetime import datetime, timedelta
from decimal import Decimal

from .accountliquidator import AccountLiquidator
from .context import Context
from .group import Group
from .liquidatablereport import LiquidatableReport, LiquidatableState
from .liquidationevent import LiquidationEvent
from .marginaccount import MarginAccount
from .observables import EventSource
from .tokenvalue import TokenValue
from .walletbalancer import WalletBalancer

# # 🥭 Liquidation Processor
#
# This file contains a liquidator processor that looks after the mechanics of liquidating an
# account.
#


# # 💧 LiquidationProcessor class
#
# An `AccountLiquidator` liquidates a `MarginAccount`. A `LiquidationProcessor` processes a
# list of `MarginAccount`s, determines if they're liquidatable, and calls an
# `AccountLiquidator` to do the work.
#


class LiquidationProcessor:
    _AGE_ERROR_THRESHOLD = timedelta(minutes=10)
    _AGE_WARNING_THRESHOLD = timedelta(minutes=5)

    def __init__(self, context: Context, account_liquidator: AccountLiquidator, wallet_balancer: WalletBalancer, worthwhile_threshold: Decimal = Decimal("0.01")):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.context: Context = context
        self.account_liquidator: AccountLiquidator = account_liquidator
        self.wallet_balancer: WalletBalancer = wallet_balancer
        self.worthwhile_threshold: Decimal = worthwhile_threshold
        self.liquidations: EventSource[LiquidationEvent] = EventSource[LiquidationEvent]()
        self.ripe_accounts: typing.Optional[typing.List[MarginAccount]] = None
        self.ripe_accounts_updated_at: datetime = datetime.now()
        self.prices_updated_at: datetime = datetime.now()

    def update_margin_accounts(self, ripe_margin_accounts: typing.List[MarginAccount]):
        self.logger.info(
            f"Received {len(ripe_margin_accounts)} ripe 🥭 margin accounts to process - prices last updated {self.prices_updated_at:%Y-%m-%d %H:%M:%S}")
        self._check_update_recency("prices", self.prices_updated_at)
        self.ripe_accounts = ripe_margin_accounts
        self.ripe_accounts_updated_at = datetime.now()

    def update_prices(self, group: Group, prices):
        started_at = time.time()

        if self.ripe_accounts is None:
            self.logger.info("Ripe accounts is None - skipping")
            return

        self.logger.info(
            f"Running on {len(self.ripe_accounts)} ripe accounts - ripe accounts last updated {self.ripe_accounts_updated_at:%Y-%m-%d %H:%M:%S}")
        self._check_update_recency("ripe account", self.ripe_accounts_updated_at)

        updated: typing.List[LiquidatableReport] = []
        for margin_account in self.ripe_accounts:
            updated += [LiquidatableReport.build(group, prices, margin_account, self.worthwhile_threshold)]

        liquidatable = list(filter(lambda report: report.state & LiquidatableState.LIQUIDATABLE, updated))
        self.logger.info(f"Of those {len(updated)}, {len(liquidatable)} are liquidatable.")

        above_water = list(filter(lambda report: report.state & LiquidatableState.ABOVE_WATER, liquidatable))
        self.logger.info(
            f"Of those {len(liquidatable)} liquidatable margin accounts, {len(above_water)} are 'above water' margin accounts with assets greater than their liabilities.")

        worthwhile = list(filter(lambda report: report.state & LiquidatableState.WORTHWHILE, above_water))
        self.logger.info(
            f"Of those {len(above_water)} above water margin accounts, {len(worthwhile)} are worthwhile margin accounts with more than ${self.worthwhile_threshold} net assets.")

        self._liquidate_all(group, prices, worthwhile)

        self.prices_updated_at = datetime.now()
        time_taken = time.time() - started_at
        self.logger.info(f"Check of all ripe 🥭 accounts complete. Time taken: {time_taken:.2f} seconds.")

    def _liquidate_all(self, group: Group, prices: typing.List[TokenValue], to_liquidate: typing.List[LiquidatableReport]):
        to_process = to_liquidate
        while len(to_process) > 0:
            highest_first = sorted(to_process,
                                   key=lambda report: report.balance_sheet.assets - report.balance_sheet.liabilities, reverse=True)
            highest = highest_first[0]
            try:
                self.account_liquidator.liquidate(highest)
                self.wallet_balancer.balance(prices)

                updated_margin_account = MarginAccount.load(self.context, highest.margin_account.address, group)
                updated_report = LiquidatableReport.build(
                    group, prices, updated_margin_account, highest.worthwhile_threshold)
                if not (updated_report.state & LiquidatableState.WORTHWHILE):
                    self.logger.info(
                        f"Margin account {updated_margin_account.address} has been drained and is no longer worthwhile.")
                else:
                    self.logger.info(
                        f"Margin account {updated_margin_account.address} is still worthwhile - putting it back on list.")
                    to_process += [updated_report]
            except Exception as exception:
                self.logger.error(f"Failed to liquidate account '{highest.margin_account.address}' - {exception}")
            finally:
                # highest should always be in to_process, but we're outside the try-except block
                # so let's be a little paranoid about it.
                if highest in to_process:
                    to_process.remove(highest)

    def _check_update_recency(self, name: str, last_updated_at: datetime) -> None:
        how_long_ago_was_last_update = datetime.now() - last_updated_at
        if how_long_ago_was_last_update > LiquidationProcessor._AGE_ERROR_THRESHOLD:
            self.logger.error(
                f"Last {name} update was {how_long_ago_was_last_update} ago - more than error threshold {LiquidationProcessor._AGE_ERROR_THRESHOLD}")
        elif how_long_ago_was_last_update > LiquidationProcessor._AGE_WARNING_THRESHOLD:
            self.logger.warning(
                f"Last {name} update was {how_long_ago_was_last_update} ago - more than warning threshold {LiquidationProcessor._AGE_WARNING_THRESHOLD}")
