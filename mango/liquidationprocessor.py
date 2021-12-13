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
import time
import typing

from datetime import datetime, timedelta
from decimal import Decimal

from .account import Account
from .accountliquidator import AccountLiquidator
from .context import Context
from .group import Group
from .instrumentvalue import InstrumentValue
from .liquidatablereport import LiquidatableReport, LiquidatableState
from .liquidationevent import LiquidationEvent
from .observables import EventSource
from .walletbalancer import WalletBalancer

# # 🥭 Liquidation Processor
#
# This file contains a liquidator processor that looks after the mechanics of liquidating an
# account.
#


# # 💧 LiquidationProcessorState enum
#
# An enum that describes the current state of the `LiquidationProcessor`.
#
class LiquidationProcessorState(enum.Enum):
    STARTING = enum.auto()
    HEALTHY = enum.auto()
    UNHEALTHY = enum.auto()

    def __str__(self) -> str:
        return self.name


# # 💧 LiquidationProcessor class
#
# An `AccountLiquidator` liquidates a `Account`. A `LiquidationProcessor` processes a
# list of `Account`s, determines if they're liquidatable, and calls an
# `AccountLiquidator` to do the work.
#
class LiquidationProcessor:
    _AGE_ERROR_THRESHOLD = timedelta(minutes=5)
    _AGE_WARNING_THRESHOLD = timedelta(minutes=2)

    def __init__(self, context: Context, name: str, account_liquidator: AccountLiquidator, wallet_balancer: WalletBalancer, worthwhile_threshold: Decimal = Decimal("0.01")) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.context: Context = context
        self.name: str = name
        self.account_liquidator: AccountLiquidator = account_liquidator
        self.wallet_balancer: WalletBalancer = wallet_balancer
        self.worthwhile_threshold: Decimal = worthwhile_threshold
        self.liquidations: EventSource[LiquidationEvent] = EventSource[LiquidationEvent]()
        self.ripe_accounts: typing.Optional[typing.Sequence[Account]] = None
        self.ripe_accounts_updated_at: datetime = datetime.now()
        self.prices_updated_at: datetime = datetime.now()
        self.state: LiquidationProcessorState = LiquidationProcessorState.STARTING
        self.state_change: EventSource[LiquidationProcessor] = EventSource[LiquidationProcessor]()

    def update_accounts(self, ripe_accounts: typing.Sequence[Account]) -> None:
        self._logger.info(
            f"Received {len(ripe_accounts)} ripe 🥭 margin accounts to process - prices last updated {self.prices_updated_at:%Y-%m-%d %H:%M:%S}")
        self._check_update_recency("prices", self.prices_updated_at)
        self.ripe_accounts = ripe_accounts
        self.ripe_accounts_updated_at = datetime.now()
        # If this is the first time through, mark ourselves as Healthy.
        if self.state == LiquidationProcessorState.STARTING:
            self.state = LiquidationProcessorState.HEALTHY

    def update_prices(self, group: Group, prices: typing.Sequence[InstrumentValue]) -> None:
        started_at = time.time()

        if self.state == LiquidationProcessorState.STARTING:
            self._logger.info("Still starting - skipping price update.")
            return

        if self.ripe_accounts is None:
            self._logger.info("Ripe accounts is None - skipping price update.")
            return

        self._logger.info(
            f"Ripe accounts last updated {self.ripe_accounts_updated_at:%Y-%m-%d %H:%M:%S}")
        self._check_update_recency("ripe account", self.ripe_accounts_updated_at)

        report: typing.List[str] = []
        updated: typing.List[LiquidatableReport] = []
        for account in self.ripe_accounts:
            updated += [LiquidatableReport.build(group, prices, account, self.worthwhile_threshold)]

        liquidatable = list(filter(lambda report: report.state & LiquidatableState.LIQUIDATABLE, updated))
        report += [f"Of those {len(updated)} ripe accounts, {len(liquidatable)} are liquidatable."]

        above_water = list(filter(lambda report: report.state & LiquidatableState.ABOVE_WATER, liquidatable))
        report += [f"Of those {len(liquidatable)} liquidatable margin accounts, {len(above_water)} have assets greater than their liabilities."]

        worthwhile = list(filter(lambda report: report.state & LiquidatableState.WORTHWHILE, above_water))
        report += [f"Of those {len(above_water)} above water margin accounts, {len(worthwhile)} are worthwhile margin accounts with more than ${self.worthwhile_threshold} net assets."]

        report_text = "\n    ".join(report)
        self._logger.info(f"""Running on {len(self.ripe_accounts)} ripe accounts:
    {report_text}""")

        self._liquidate_all(group, prices, worthwhile)

        self.prices_updated_at = datetime.now()
        time_taken = time.time() - started_at
        self._logger.info(f"Check of all ripe 🥭 accounts complete. Time taken: {time_taken:.2f} seconds.")

    def _liquidate_all(self, group: Group, prices: typing.Sequence[InstrumentValue], to_liquidate: typing.Sequence[LiquidatableReport]) -> None:
        to_process = list(to_liquidate)
        while len(to_process) > 0:
            # TODO - sort this when LiquidationReport has the proper details for V3.
            # highest_first = sorted(to_process,
            #                        key=lambda report: report.balance_sheet.assets - report.balance_sheet.liabilities, reverse=True)
            highest_first = to_process
            highest = highest_first[0]
            try:
                self.account_liquidator.liquidate(highest)
                self.wallet_balancer.balance(self.context, prices)

                updated_account = Account.load(self.context, highest.account.address, group)
                updated_report = LiquidatableReport.build(
                    group, prices, updated_account, highest.worthwhile_threshold)
                if not (updated_report.state & LiquidatableState.WORTHWHILE):
                    self._logger.info(
                        f"Margin account {updated_account.address} has been drained and is no longer worthwhile.")
                else:
                    self._logger.info(
                        f"Margin account {updated_account.address} is still worthwhile - putting it back on list.")
                    to_process += [updated_report]
            except Exception as exception:
                self._logger.error(
                    f"[{self.name}] Failed to liquidate account '{highest.account.address}' - {exception}.")
            finally:
                # highest should always be in to_process, but we're outside the try-except block
                # so let's be a little paranoid about it.
                self._logger.info(f"Liquidatable accounts to process was: {len(to_process)}")
                if highest in to_process:
                    to_process.remove(highest)
                self._logger.info(f"Liquidatable accounts to process is now: {len(to_process)}")

    def _check_update_recency(self, name: str, last_updated_at: datetime) -> None:
        how_long_ago_was_last_update = datetime.now() - last_updated_at
        if how_long_ago_was_last_update > LiquidationProcessor._AGE_ERROR_THRESHOLD:
            self.state = LiquidationProcessorState.UNHEALTHY
            self.state_change.on_next(self)
            self._logger.error(
                f"[{self.name}] Liquidator - last {name} update was {how_long_ago_was_last_update} ago - more than error threshold {LiquidationProcessor._AGE_ERROR_THRESHOLD}")
        elif how_long_ago_was_last_update > LiquidationProcessor._AGE_WARNING_THRESHOLD:
            self._logger.warning(
                f"[{self.name}] Liquidator - last {name} update was {how_long_ago_was_last_update} ago - more than warning threshold {LiquidationProcessor._AGE_WARNING_THRESHOLD}")
