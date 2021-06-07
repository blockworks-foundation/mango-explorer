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

from .context import Context
from .group import Group
from .instructions import ForceCancelOrdersInstructionBuilder, InstructionBuilder, LiquidateInstructionBuilder
from .liquidationevent import LiquidationEvent
from .marginaccount import MarginAccount, MarginAccountMetadata
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
    def prepare_instructions(self, group: Group, margin_account: MarginAccount, prices: typing.List[TokenValue]) -> typing.List[InstructionBuilder]:
        raise NotImplementedError("AccountLiquidator.prepare_instructions() is not implemented on the base type.")

    @abc.abstractmethod
    def liquidate(self, group: Group, margin_account: MarginAccount, prices: typing.List[TokenValue]) -> typing.Optional[str]:
        raise NotImplementedError("AccountLiquidator.liquidate() is not implemented on the base type.")


# # 🌬️ NullAccountLiquidator class
#
# A 'null', 'no-op', 'dry run' implementation of the `AccountLiquidator` class.
#


class NullAccountLiquidator(AccountLiquidator):
    def __init__(self):
        super().__init__()

    def prepare_instructions(self, group: Group, margin_account: MarginAccount, prices: typing.List[TokenValue]) -> typing.List[InstructionBuilder]:
        return []

    def liquidate(self, group: Group, margin_account: MarginAccount, prices: typing.List[TokenValue]) -> typing.Optional[str]:
        self.logger.info(f"Skipping liquidation of margin account [{margin_account.address}]")
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

    def prepare_instructions(self, group: Group, margin_account: MarginAccount, prices: typing.List[TokenValue]) -> typing.List[InstructionBuilder]:
        liquidate_instructions: typing.List[InstructionBuilder] = []
        liquidate_instruction = LiquidateInstructionBuilder.from_margin_account_and_market(
            self.context, group, self.wallet, margin_account, prices)
        if liquidate_instruction is not None:
            liquidate_instructions += [liquidate_instruction]

        return liquidate_instructions

    def liquidate(self, group: Group, margin_account: MarginAccount, prices: typing.List[TokenValue]) -> typing.Optional[str]:
        instruction_builders = self.prepare_instructions(group, margin_account, prices)

        if len(instruction_builders) == 0:
            return None

        transaction = Transaction()
        for builder in instruction_builders:
            transaction.add(builder.build())

        for instruction in transaction.instructions:
            self.logger.debug("INSTRUCTION")
            self.logger.debug("    Keys:")
            for key in instruction.keys:
                self.logger.debug("        ", f"{key.pubkey}".ljust(
                    45), f"{key.is_signer}".ljust(6), f"{key.is_writable}".ljust(6))
            self.logger.debug("    Data:", " ".join(f"{x:02x}" for x in instruction.data))
            self.logger.debug("    Program ID:", instruction.program_id)

        transaction_response = self.context.client.send_transaction(transaction, self.wallet.account)
        transaction_id = self.context.unwrap_transaction_id_or_raise_exception(transaction_response)
        return transaction_id


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

    def prepare_instructions(self, group: Group, margin_account: MarginAccount, prices: typing.List[TokenValue]) -> typing.List[InstructionBuilder]:
        force_cancel_orders_instructions: typing.List[InstructionBuilder] = []
        for index, market_metadata in enumerate(group.markets):
            open_orders = margin_account.open_orders_accounts[index]
            if open_orders is not None:
                market = market_metadata.fetch_market(self.context)
                orders = market.load_orders_for_owner(margin_account.owner)
                order_count = len(orders)
                if order_count > 0:
                    force_cancel_orders_instructions += ForceCancelOrdersInstructionBuilder.multiple_instructions_from_margin_account_and_market(
                        self.context, group, self.wallet, margin_account, market_metadata, order_count)

        all_instructions = force_cancel_orders_instructions + super().prepare_instructions(group, margin_account, prices)

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

    def prepare_instructions(self, group: Group, margin_account: MarginAccount, prices: typing.List[TokenValue]) -> typing.List[InstructionBuilder]:
        return self.inner.prepare_instructions(group, margin_account, prices)

    def liquidate(self, group: Group, margin_account: MarginAccount, prices: typing.List[TokenValue]) -> typing.Optional[str]:
        balance_sheet = margin_account.get_balance_sheet_totals(group, prices)
        balances = margin_account.get_intrinsic_balances(group)
        mam = MarginAccountMetadata(margin_account, balance_sheet, balances)

        balances_before = group.fetch_balances(self.wallet.address)
        self.logger.info("Wallet balances before:")
        TokenValue.report(self.logger.info, balances_before)

        self.logger.info(f"Margin account balances before:\n{mam.balances}")
        self.logger.info(f"Liquidating margin account: {mam.margin_account}\n{mam.balance_sheet}")
        transaction_id = self.inner.liquidate(group, mam.margin_account, prices)
        if transaction_id is None:
            self.logger.info("No transaction sent.")
        else:
            self.logger.info(f"Transaction ID: {transaction_id} - waiting for confirmation...")

            response = self.context.wait_for_confirmation(transaction_id)
            if response is None:
                self.logger.warning(
                    f"Could not process 'after' liquidation stage - no data for transaction {transaction_id}")
                return transaction_id

            transaction_scout = TransactionScout.from_transaction_response(self.context, response)

            group_after = Group.load(self.context)
            margin_account_after_liquidation = MarginAccount.load(self.context, mam.margin_account.address, group_after)
            intrinsic_balances_after = margin_account_after_liquidation.get_intrinsic_balances(group_after)
            self.logger.info(f"Margin account balances after: {intrinsic_balances_after}")

            self.logger.info("Wallet Balances After:")
            balances_after = group_after.fetch_balances(self.wallet.address)
            TokenValue.report(self.logger.info, balances_after)

            liquidation_event = LiquidationEvent(datetime.datetime.now(),
                                                 self.liquidator_name,
                                                 self.context.group_name,
                                                 transaction_scout.succeeded,
                                                 transaction_id,
                                                 self.wallet.address,
                                                 margin_account_after_liquidation.address,
                                                 balances_before,
                                                 balances_after)

            self.logger.info("Wallet Balances Changes:")
            changes = TokenValue.changes(balances_before, balances_after)
            TokenValue.report(self.logger.info, changes)

            self.liquidations_publisher.publish(liquidation_event)

        return transaction_id
