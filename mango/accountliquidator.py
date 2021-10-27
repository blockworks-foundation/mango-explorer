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


import abc
import datetime
import logging
import typing

from solana.transaction import Transaction

from .client import TransactionException
from .context import Context
from .group import Group
from .instructions import ForceCancelOrdersInstructionBuilder, InstructionBuilder, LiquidateInstructionBuilder
from .liquidatablereport import LiquidatableReport
from .liquidationevent import LiquidationEvent
from .marginaccount import MarginAccount
from .observables import EventSource
from .tokenvalue import TokenValue
from .transactionscout import TransactionScout
from .wallet import Wallet


# # 🥭 AccountLiquidator
#
# An `AccountLiquidator` liquidates a `MarginAccount`, if possible.
#
# The follows the common pattern of having an abstract base class that defines the interface
# external code should use, along with a 'null' implementation and at least one full
# implementation.
#
# The idea is that preparing code can choose whether to use the null implementation (in the
# case of a 'dry run' for instance) or the full implementation, but the code that defines
# the algorithm - which actually calls the `AccountLiquidator` - doesn't have to care about
# this choice.
#

# # 💧 AccountLiquidator class
#
# This abstract base class defines the interface to account liquidators, which in this case
# is just the `liquidate()` method.
#


class AccountLiquidator(metaclass=abc.ABCMeta):
    def __init__(self):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def prepare_instructions(self, liquidatable_report: LiquidatableReport) -> typing.List[InstructionBuilder]:
        raise NotImplementedError("AccountLiquidator.prepare_instructions() is not implemented on the base type.")

    @abc.abstractmethod
    def liquidate(self, liquidatable_report: LiquidatableReport) -> typing.Optional[typing.Sequence[str]]:
        raise NotImplementedError("AccountLiquidator.liquidate() is not implemented on the base type.")


# # 🌬️ NullAccountLiquidator class
#
# A 'null', 'no-op', 'dry run' implementation of the `AccountLiquidator` class.
#


class NullAccountLiquidator(AccountLiquidator):
    def __init__(self):
        super().__init__()

    def prepare_instructions(self, liquidatable_report: LiquidatableReport) -> typing.List[InstructionBuilder]:
        return []

    def liquidate(self, liquidatable_report: LiquidatableReport) -> typing.Optional[typing.Sequence[str]]:
        self.logger.info(f"Skipping liquidation of margin account [{liquidatable_report.margin_account.address}]")
        return None


# # 💧 ActualAccountLiquidator class
#
# This full implementation takes a `MarginAccount` and liquidates it.
#
# It can also serve as a base class for further derivation. Derived classes may override
# `prepare_instructions()` to extend the liquidation process (for example to cancel
# outstanding orders before liquidating).
#

class ActualAccountLiquidator(AccountLiquidator):
    def __init__(self, context: Context, wallet: Wallet):
        super().__init__()
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.context = context
        self.wallet = wallet

    def prepare_instructions(self, liquidatable_report: LiquidatableReport) -> typing.List[InstructionBuilder]:
        liquidate_instructions: typing.List[InstructionBuilder] = []
        liquidate_instruction = LiquidateInstructionBuilder.from_margin_account_and_market(
            self.context, liquidatable_report.group, self.wallet, liquidatable_report.margin_account, liquidatable_report.prices)
        if liquidate_instruction is not None:
            liquidate_instructions += [liquidate_instruction]

        return liquidate_instructions

    def liquidate(self, liquidatable_report: LiquidatableReport) -> typing.Optional[typing.Sequence[str]]:
        instruction_builders = self.prepare_instructions(liquidatable_report)

        if len(instruction_builders) == 0:
            return None

        transaction = Transaction()
        for builder in instruction_builders:
            transaction.add(builder.build())

        transaction_id: str = self.context.client.send_transaction(transaction, self.wallet.keypair)
        return [transaction_id]


# # 🌪️ ForceCancelOrdersAccountLiquidator class
#
# When liquidating an account, it's a good idea to ensure it has no open orders that could
# lock funds. This is why Mango allows a liquidator to force-close orders on a liquidatable
# account.
#
# `ForceCancelOrdersAccountLiquidator` overrides `prepare_instructions()` to inject any
# necessary force-cancel instructions before the `PartialLiquidate` instruction.
#
# This is not always necessary. For example, if the liquidator is partially-liquidating a
# large account, then perhaps only the first partial-liquidate needs to check and force-close
# orders, and subsequent partial liquidations can skip this step as an optimisation.
#
# The separation of the regular `AccountLiquidator` and the
# `ForceCancelOrdersAccountLiquidator` classes allows the caller to determine which process
# is used.
#


class ForceCancelOrdersAccountLiquidator(ActualAccountLiquidator):
    def __init__(self, context: Context, wallet: Wallet):
        super().__init__(context, wallet)

    def prepare_instructions(self, liquidatable_report: LiquidatableReport) -> typing.List[InstructionBuilder]:
        force_cancel_orders_instructions: typing.List[InstructionBuilder] = []
        for index, market_metadata in enumerate(liquidatable_report.group.markets):
            open_orders = liquidatable_report.margin_account.open_orders_accounts[index]
            if open_orders is not None:
                market = market_metadata.fetch_market(self.context)
                orders = market.load_orders_for_owner(liquidatable_report.margin_account.owner)
                order_count = len(orders)
                if order_count > 0:
                    force_cancel_orders_instructions += ForceCancelOrdersInstructionBuilder.multiple_instructions_from_margin_account_and_market(
                        self.context, liquidatable_report.group, self.wallet, liquidatable_report.margin_account, market_metadata, order_count)

        all_instructions = force_cancel_orders_instructions + super().prepare_instructions(liquidatable_report)

        return all_instructions


# 📝 ReportingAccountLiquidator class
#
# This class takes a regular `AccountLiquidator` and wraps its `liquidate()` call in some
# useful reporting.
#

class ReportingAccountLiquidator(AccountLiquidator):
    def __init__(self, inner: AccountLiquidator, context: Context, wallet: Wallet, liquidations_publisher: EventSource[LiquidationEvent], liquidator_name: str):
        super().__init__()
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.inner: AccountLiquidator = inner
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.liquidations_publisher: EventSource[LiquidationEvent] = liquidations_publisher
        self.liquidator_name: str = liquidator_name

    def prepare_instructions(self, liquidatable_report: LiquidatableReport) -> typing.List[InstructionBuilder]:
        return self.inner.prepare_instructions(liquidatable_report)

    def liquidate(self, liquidatable_report: LiquidatableReport) -> typing.Optional[typing.Sequence[str]]:
        balances_before = liquidatable_report.group.fetch_balances(self.context, self.wallet.address)
        self.logger.info("Wallet balances before:")
        TokenValue.report(balances_before, self.logger.info)

        self.logger.info(
            f"Liquidating margin account {liquidatable_report.margin_account.address}:\n{liquidatable_report}\n{liquidatable_report.margin_account}")
        try:
            transaction_ids = self.inner.liquidate(liquidatable_report)
        except TransactionException as exception:
            self.logger.warning(f"Account was not liquidatable:\n{exception}")
            # It would be nice if we had a strongly-typed way of checking this.
            if "MangoErrorCode::NotLiquidatable" in str("".join(exception.logs)):
                failed_liquidation_event = LiquidationEvent(datetime.datetime.now(),
                                                            self.liquidator_name,
                                                            self.context.group_name,
                                                            False,
                                                            "",
                                                            self.wallet.address,
                                                            liquidatable_report.margin_account.address,
                                                            balances_before,
                                                            balances_before)
                self.liquidations_publisher.publish(failed_liquidation_event)
                return None
            raise exception

        if transaction_ids is None or len(transaction_ids) == 0:
            self.logger.info("No transaction sent.")
            return None

        self.logger.info(f"Transaction IDs: {transaction_ids} - waiting for confirmation...")

        transactions = self.context.client.wait_for_confirmation(transaction_ids)
        if transactions is None:
            self.logger.warning(
                f"Could not process 'after' liquidation stage - no data for transaction {transaction_ids}")
            return transaction_ids

        all_succeeded: bool = True
        for individual_response in transactions:
            transaction_scout = TransactionScout.from_transaction_response(self.context, individual_response)
            if not transaction_scout.succeeded:
                all_succeeded = False

        group_after = Group.load(self.context)
        margin_account_after_liquidation = MarginAccount.load(
            self.context, liquidatable_report.margin_account.address, group_after)
        intrinsic_balances_after = margin_account_after_liquidation.get_intrinsic_balances(group_after)
        self.logger.info("Margin account balances after:")
        TokenValue.report(intrinsic_balances_after, self.logger.info)

        self.logger.info("Wallet Balances After:")
        balances_after = group_after.fetch_balances(self.context, self.wallet.address)
        TokenValue.report(balances_after, self.logger.info)

        liquidation_event = LiquidationEvent(datetime.datetime.now(),
                                             self.liquidator_name,
                                             self.context.group_name,
                                             all_succeeded,
                                             transaction_ids,
                                             self.wallet.address,
                                             margin_account_after_liquidation.address,
                                             balances_before,
                                             balances_after)

        self.logger.info("Wallet Balances Changes:")
        changes = TokenValue.changes(balances_before, balances_after)
        TokenValue.report(changes, self.logger.info)

        self.liquidations_publisher.publish(liquidation_event)

        if all_succeeded:
            return transaction_ids
        return None
