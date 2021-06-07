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
import logging
import typing

from decimal import Decimal

from .context import Context
from .token import Token
from .tokenvalue import TokenValue
from .tradeexecutor import TradeExecutor
from .wallet import Wallet


# # 🥭 WalletBalancer
#
# This notebook deals with balancing a wallet after processing liquidations, so that it has
# appropriate funds for the next liquidation.
#
# We want to be able to maintain liquidity in our wallet. For instance if there are a lot of
# ETH shorts being liquidated, we'll need to supply ETH, but what do we do when we run out
# of ETH and there are still liquidations to perform?
#
# We 'balance' our wallet tokens, buying or selling or swapping them as required.
#

# # 🥭 Target Balances
#
# To be able to maintain the right balance of tokens, we need to know what the right
# balance is. Different people have different opinions, and we don't all have the same
# value in our liquidator accounts, so we need a way to allow whoever is running the
# liquidator to specify what the target token balances should be.
#
# There are two possible approaches to specifying the target value:
# * A 'fixed' value, like 10 ETH
# * A 'percentage' value, like 20% ETH
#
# Percentage is trickier, because to come up with the actual target we need to take into
# account the wallet value and the current price of the target token.
#
# The way this all hangs together is:
# * A parser parses string values (probably from a command-line) into `TargetBalance`
#   objects.
# * There are two types of `TargetBalance` objects - `FixedTargetBalance` and
#   `PercentageTargetBalance`.
# * To get the actual `TokenValue` for balancing, the `TargetBalance` must be 'resolved'
#   by calling `resolve()` with the appropriate token price and wallet value.
#

# # 🥭 TargetBalance class
#
# This is the abstract base class for our target balances, to allow them to be treated polymorphically.
#


class TargetBalance(metaclass=abc.ABCMeta):
    def __init__(self, token: Token):
        self.token = token

    @abc.abstractmethod
    def resolve(self, current_price: Decimal, total_value: Decimal) -> TokenValue:
        raise NotImplementedError("TargetBalance.resolve() is not implemented on the base type.")

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 FixedTargetBalance class
#
# This is the simple case, where the `FixedTargetBalance` object contains enough information on its own to build the resolved `TokenValue` object.
#

class FixedTargetBalance(TargetBalance):
    def __init__(self, token: Token, value: Decimal):
        super().__init__(token)
        self.value = value

    def resolve(self, current_price: Decimal, total_value: Decimal) -> TokenValue:
        return TokenValue(self.token, self.value)

    def __str__(self) -> str:
        return f"""« FixedTargetBalance [{self.value} {self.token.name}] »"""


# # 🥭 PercentageTargetBalance
#
# This is the more complex case, where the target is a percentage of the total wallet
# balance.
#
# So, to actually calculate the right target, we need to know the total wallet balance and
# the current price. Once we have those the calculation is just:
# >
# > _wallet fraction_ is _percentage_ of _wallet value_
# >
# > _target balance_ is _wallet fraction_ divided by _token price_
#

class PercentageTargetBalance(TargetBalance):
    def __init__(self, token: Token, target_percentage: Decimal):
        super().__init__(token)
        self.target_fraction = target_percentage / 100

    def resolve(self, current_price: Decimal, total_value: Decimal) -> TokenValue:
        target_value = total_value * self.target_fraction
        target_size = target_value / current_price
        return TokenValue(self.token, target_size)

    def __str__(self) -> str:
        return f"""« PercentageTargetBalance [{self.target_fraction * 100}% {self.token.name}] »"""


# # 🥭 TargetBalanceParser class
#
# The `TargetBalanceParser` takes a string like "BTC:0.2" or "ETH:20%" and returns the appropriate TargetBalance object.
#
# This has a lot of manual error handling because it's likely the error messages will be seen by people and so we want to be as clear as we can what specifically is wrong.
#

class TargetBalanceParser:
    def __init__(self, tokens: typing.List[Token]):
        self.tokens = tokens

    def parse(self, to_parse: str) -> TargetBalance:
        try:
            token_name, value = to_parse.split(":")
        except Exception as exception:
            raise Exception(f"Could not parse target balance '{to_parse}'") from exception

        token = Token.find_by_symbol(self.tokens, token_name)

        # The value we have may be an int (like 27), a fraction (like 0.1) or a percentage
        # (like 25%). In all cases we want the number as a number, but we also want to know if
        # we have a percent or not
        values = value.split("%")
        numeric_value_string = values[0]
        try:
            numeric_value = Decimal(numeric_value_string)
        except Exception as exception:
            raise Exception(
                f"Could not parse '{numeric_value_string}' as a decimal number. It should be formatted as a decimal number, e.g. '2.345', with no surrounding spaces.") from exception

        if len(values) > 2:
            raise Exception(
                f"Could not parse '{value}' as a decimal percentage. It should be formatted as a decimal number followed by a percentage sign, e.g. '30%', with no surrounding spaces.")

        if len(values) == 1:
            return FixedTargetBalance(token, numeric_value)
        else:
            return PercentageTargetBalance(token, numeric_value)


# # 🥭 sort_changes_for_trades function
#
# It's important to process SELLs first, so we have enough funds in the quote balance for the
# BUYs.
#
# It looks like this function takes size into account, but it doesn't really - 2 ETH is
# smaller than 1 BTC (for now?) but the value 2 will be treated as bigger than 1. We don't
# really care that much as long as we have SELLs before BUYs. (We could, later, take price
# into account for this sorting but we don't need to now so we don't.)
#

def sort_changes_for_trades(changes: typing.List[TokenValue]) -> typing.List[TokenValue]:
    return sorted(changes, key=lambda change: change.value)


# # 🥭 calculate_required_balance_changes function
#
# Takes a list of current balances, and a list of desired balances, and returns the list of changes required to get us to the desired balances.
#


def calculate_required_balance_changes(current_balances: typing.List[TokenValue], desired_balances: typing.List[TokenValue]) -> typing.List[TokenValue]:
    changes: typing.List[TokenValue] = []
    for desired in desired_balances:
        current = TokenValue.find_by_token(current_balances, desired.token)
        change = TokenValue(desired.token, desired.value - current.value)
        changes += [change]

    return changes


# # 🥭 FilterSmallChanges class
#
# Allows us to filter out changes that aren't worth the effort.
#
# For instance, if our desired balance requires changing less than 1% of our total balance,
# it may not be worth bothering with right not.
#
# Calculations are based on the total wallet balance, rather than the magnitude of the
# change per-token, because a change of 0.01 of one token may be worth more than a change
# of 10 in another token. Normalising values to our wallet balance makes these changes
# easier to reason about.
#


class FilterSmallChanges:
    def __init__(self, action_threshold: Decimal, balances: typing.List[TokenValue], prices: typing.List[TokenValue]):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.prices: typing.Dict[str, TokenValue] = {}
        total = Decimal(0)
        for balance in balances:
            price = TokenValue.find_by_token(prices, balance.token)
            self.prices[f"{price.token.mint}"] = price
            total += price.value * balance.value
        self.total_balance = total
        self.action_threshold_value = total * action_threshold
        self.logger.info(
            f"Wallet total balance of {total} gives action threshold value of {self.action_threshold_value}")

    def allow(self, token_value: TokenValue) -> bool:
        price = self.prices[f"{token_value.token.mint}"]
        value = price.value * token_value.value
        absolute_value = value.copy_abs()
        result = absolute_value > self.action_threshold_value

        self.logger.info(
            f"Value of {token_value.token.name} trade is {absolute_value}, threshold value is {self.action_threshold_value}. Is this worth doing? {result}.")
        return result


# # 🥭 WalletBalancers
#
# We want two types of this class:
# * A 'null' implementation that adheres to the interface but doesn't do anything, and
# * A 'live' implementation that actually does the balancing.
#
# This allows us to have code that implements logic including wallet balancing, without
# having to worry about whether the user wants to re-balance or not - we can just plug
# in the 'null' variant and the logic all still works.
#
# To have this work we define an abstract base class `WalletBalancer` which defines the
# interface, then a `NullWalletBalancer` which adheres to this interface but doesn't
# perform any action, and finally the real `LiveWalletBalancer` which can perform the
# balancing action.
#

# # 🥭 WalletBalancer class
#
# This is the abstract class which defines the interface.
#

class WalletBalancer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def balance(self, prices: typing.List[TokenValue]):
        raise NotImplementedError("WalletBalancer.balance() is not implemented on the base type.")


# # 🥭 NullWalletBalancer class
#
# This is the 'empty', 'no-op', 'dry run' wallet balancer which doesn't do anything but
# which can be plugged into algorithms that may want balancing logic.
#


class NullWalletBalancer(WalletBalancer):
    def balance(self, prices: typing.List[TokenValue]):
        pass


# # 🥭 LiveWalletBalancer class
#
# This is the high-level class that does much of the work.
#

class LiveWalletBalancer(WalletBalancer):
    def __init__(self, context: Context, wallet: Wallet, trade_executor: TradeExecutor, action_threshold: Decimal, tokens: typing.List[Token], target_balances: typing.List[TargetBalance]):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.trade_executor: TradeExecutor = trade_executor
        self.action_threshold: Decimal = action_threshold
        self.tokens: typing.List[Token] = tokens
        self.target_balances: typing.List[TargetBalance] = target_balances

    def balance(self, prices: typing.List[TokenValue]):
        padding = "\n    "

        def balances_report(balances) -> str:
            return padding.join(list([f"{bal}" for bal in balances]))

        current_balances = self._fetch_balances()
        total_value = Decimal(0)
        for bal in current_balances:
            price = TokenValue.find_by_token(prices, bal.token)
            value = bal.value * price.value
            total_value += value
        self.logger.info(f"Starting balances: {padding}{balances_report(current_balances)} - total: {total_value}")
        resolved_targets: typing.List[TokenValue] = []
        for target in self.target_balances:
            price = TokenValue.find_by_token(prices, target.token)
            resolved_targets += [target.resolve(price.value, total_value)]

        balance_changes = calculate_required_balance_changes(current_balances, resolved_targets)
        self.logger.info(f"Full balance changes: {padding}{balances_report(balance_changes)}")

        dont_bother = FilterSmallChanges(self.action_threshold, current_balances, prices)
        filtered_changes = list(filter(dont_bother.allow, balance_changes))
        self.logger.info(f"Filtered balance changes: {padding}{balances_report(filtered_changes)}")
        if len(filtered_changes) == 0:
            self.logger.info("No balance changes to make.")
            return

        sorted_changes = sort_changes_for_trades(filtered_changes)
        self._make_changes(sorted_changes)
        updated_balances = self._fetch_balances()
        self.logger.info(f"Finishing balances: {padding}{balances_report(updated_balances)}")

    def _make_changes(self, balance_changes: typing.List[TokenValue]):
        self.logger.info(f"Balance changes to make: {balance_changes}")
        for change in balance_changes:
            if change.value < 0:
                self.trade_executor.sell(change.token.name, change.value.copy_abs())
            else:
                self.trade_executor.buy(change.token.name, change.value.copy_abs())

    def _fetch_balances(self) -> typing.List[TokenValue]:
        balances: typing.List[TokenValue] = []
        for token in self.tokens:
            balance = TokenValue.fetch_total_value(self.context, self.wallet.address, token)
            balances += [balance]

        return balances
