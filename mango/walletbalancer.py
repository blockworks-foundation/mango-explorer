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

from .account import Account
from .context import Context
from .group import Group
from .token import Instrument, Token
from .instrumentvalue import InstrumentValue
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
# * To get the actual `InstrumentValue` for balancing, the `TargetBalance` must be 'resolved'
#   by calling `resolve()` with the appropriate token price and wallet value.
#

# # 🥭 TargetBalance class
#
# This is the abstract base class for our target balances, to allow them to be treated polymorphically.
#
class TargetBalance(metaclass=abc.ABCMeta):
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol.upper()

    @abc.abstractmethod
    def resolve(self, instrument: Instrument, current_price: Decimal, total_value: Decimal) -> InstrumentValue:
        raise NotImplementedError("TargetBalance.resolve() is not implemented on the base type.")

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 FixedTargetBalance class
#
# This is the simple case, where the `FixedTargetBalance` object contains enough information on its own to build the resolved `InstrumentValue` object.
#
class FixedTargetBalance(TargetBalance):
    def __init__(self, symbol: str, value: Decimal) -> None:
        super().__init__(symbol)
        self.value = value

    def resolve(self, instrument: Instrument, current_price: Decimal, total_value: Decimal) -> InstrumentValue:
        return InstrumentValue(instrument, self.value)

    def __str__(self) -> str:
        return f"""« FixedTargetBalance [{self.value} {self.symbol}] »"""


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
    def __init__(self, symbol: str, target_percentage: Decimal) -> None:
        super().__init__(symbol)
        self.target_fraction = target_percentage / 100

    def resolve(self, instrument: Instrument, current_price: Decimal, total_value: Decimal) -> InstrumentValue:
        target_value = total_value * self.target_fraction
        target_size = target_value / current_price
        return InstrumentValue(instrument, target_size)

    def __str__(self) -> str:
        return f"""« PercentageTargetBalance [{self.target_fraction * 100}% {self.symbol}] »"""


# # 🥭 parse_target_balance function
#
# `argparse` handler for `TargetBalance` parsing. Can be used like:
# parser.add_argument("--target", type=mango.parse_target_balance, action="append", required=True,
#                     help="token symbol plus target value or percentage, separated by a colon (e.g. 'ETH:2.5')")
#
def parse_target_balance(to_parse: str) -> TargetBalance:
    try:
        symbol, value = to_parse.split(":")
    except Exception as exception:
        raise Exception(f"Could not parse target balance '{to_parse}'") from exception

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
        return FixedTargetBalance(symbol, numeric_value)
    else:
        return PercentageTargetBalance(symbol, numeric_value)


# # 🥭 parse_fixed_target_balance function
#
# `argparse` handler for `TargetBalance` parsing. Can only be used for `FixedTargetBalance`s - will raise an
# error if a `PercentageTargetBalance` is attempted. This is useful for circumstances where percentage
# balance targets aren't allowed.
#
# Can be used like:
# parser.add_argument("--target", type=mango.parse_fixed_target_balance, action="append", required=True,
#                     help="token symbol plus target value or percentage, separated by a colon (e.g. 'ETH:2.5')")
#
def parse_fixed_target_balance(to_parse: str) -> TargetBalance:
    try:
        symbol, value = to_parse.split(":")
    except Exception as exception:
        raise Exception(f"Could not parse target balance '{to_parse}'") from exception

    # The value we have may be an int (like 27)or  a fraction (like 0.1). In all cases we want the number
    # as a number, but we also want to know if we have a percent or not so we can raise an exception.
    values = value.split("%")
    if len(values) > 1:
        raise Exception(
            f"Could not parse '{value}' as a decimal target. (Percentage targets are not allowed in this context.)")

    numeric_value_string = values[0]
    try:
        numeric_value = Decimal(numeric_value_string)
    except Exception as exception:
        raise Exception(
            f"Could not parse '{numeric_value_string}' as a decimal number. It should be formatted as a decimal number, e.g. '2.345', with no surrounding spaces.") from exception

    return FixedTargetBalance(symbol, numeric_value)


# # 🥭 sort_changes_for_trades function
#
# It's important to process SELLs first, so we have enough funds in the quote balance for the
# BUYs.
#
# It looks like this function takes size into account, but it doesn't really - 2 ETH is
# smaller than 1 BTC (for now?) but the value 2 will be treated as bigger than 1. We don't
# really care that much as long as we have SELLs before BUYs. (We could, later, take price
# into account for this sorting but we don't need to now so we don't.)
#
def sort_changes_for_trades(changes: typing.Sequence[InstrumentValue]) -> typing.Sequence[InstrumentValue]:
    return sorted(changes, key=lambda change: change.value)


# # 🥭 calculate_required_balance_changes function
#
# Takes a list of current balances, and a list of desired balances, and returns the list of changes required to get us to the desired balances.
#
def calculate_required_balance_changes(current_balances: typing.Sequence[InstrumentValue], desired_balances: typing.Sequence[InstrumentValue]) -> typing.Sequence[InstrumentValue]:
    changes: typing.List[InstrumentValue] = []
    for desired in desired_balances:
        current = InstrumentValue.find_by_token(current_balances, desired.token)
        change = InstrumentValue(desired.token, desired.value - current.value)
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
    def __init__(self, action_threshold: Decimal, balances: typing.Sequence[InstrumentValue],
                 prices: typing.Sequence[InstrumentValue]) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.prices: typing.Dict[str, InstrumentValue] = {}
        total = Decimal(0)
        for balance in balances:
            price = InstrumentValue.find_by_token(prices, balance.token)
            self.prices[price.token.symbol] = price
            total += price.value * balance.value
        self.total_balance = total
        self.action_threshold_value = total * action_threshold
        self._logger.info(
            f"Wallet total balance of {total:,.8f} gives action threshold: {self.action_threshold_value:,.8f}")

    def allow(self, token_value: InstrumentValue) -> bool:
        price = self.prices[token_value.token.symbol]
        value = price.value * token_value.value
        absolute_value = value.copy_abs()
        result = absolute_value > self.action_threshold_value

        self._logger.info(
            f"Worth doing? {result}. {token_value.token.name} trade is worth: {absolute_value:,.8f}, threshold is: {self.action_threshold_value:,.8f}.")
        return result


# # 🥭 WalletBalancers
#
# We want two types of this class:
# * 'null' implementation that adheres to the interface but doesn't do anything, and
# * 'live' implementations that actually do the balancing.
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
    def __init__(self) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def balance(self, context: Context, prices: typing.Sequence[InstrumentValue]) -> None:
        raise NotImplementedError("WalletBalancer.balance() is not implemented on the base type.")


# # 🥭 NullWalletBalancer class
#
# This is the 'empty', 'no-op', 'dry run' wallet balancer which doesn't do anything but
# which can be plugged into algorithms that may want balancing logic.
#
class NullWalletBalancer(WalletBalancer):
    def __init__(self) -> None:
        super().__init__()

    def balance(self, context: Context, prices: typing.Sequence[InstrumentValue]) -> None:
        pass


# # 🥭 LiveWalletBalancer class
#
# This is the high-level class that does much of the work.
#
class LiveWalletBalancer(WalletBalancer):
    def __init__(self, wallet: Wallet, quote_token: Token, trade_executor: TradeExecutor,
                 targets: typing.Sequence[TargetBalance], action_threshold: Decimal) -> None:
        super().__init__()
        self.wallet: Wallet = wallet
        self.quote_token: Token = quote_token
        self.trade_executor: TradeExecutor = trade_executor
        self.targets: typing.Sequence[TargetBalance] = targets
        self.action_threshold: Decimal = action_threshold

    def balance(self, context: Context, prices: typing.Sequence[InstrumentValue]) -> None:
        padding = "\n    "

        def balances_report(balances: typing.Sequence[InstrumentValue]) -> str:
            return padding.join(list([f"{bal}" for bal in balances]))

        tokens: typing.List[Token] = []
        for target_balance in self.targets:
            token = context.instrument_lookup.find_by_symbol(target_balance.symbol)
            if token is None:
                raise Exception(f"Could not find details of token {target_balance.symbol}.")
            tokens += [Token.ensure(token)]
        tokens += [self.quote_token]

        balances = self._fetch_balances(context, tokens)
        total_value = Decimal(0)
        for bal in balances:
            price = InstrumentValue.find_by_token(prices, bal.token)
            value = bal.value * price.value
            total_value += value
        self._logger.info(f"Starting balances: {padding}{balances_report(balances)}")
        total_token_value: InstrumentValue = InstrumentValue(self.quote_token, total_value)
        self._logger.info(f"Total: {total_token_value}")

        resolved_targets: typing.List[InstrumentValue] = []
        for target in self.targets:
            price = InstrumentValue.find_by_symbol(prices, target.symbol)
            resolved_targets += [target.resolve(price.token, price.value, total_value)]

        balance_changes = calculate_required_balance_changes(balances, resolved_targets)
        self._logger.info(f"Desired balance changes: {padding}{balances_report(balance_changes)}")

        dont_bother = FilterSmallChanges(self.action_threshold, balances, prices)
        filtered_changes = list(filter(dont_bother.allow, balance_changes))
        self._logger.info(f"Filtered balance changes: {padding}{balances_report(filtered_changes)}")
        if len(filtered_changes) == 0:
            self._logger.info("No balance changes to make.")
            return

        sorted_changes = sort_changes_for_trades(filtered_changes)
        self._make_changes(sorted_changes)
        updated_balances = self._fetch_balances(context, tokens)
        self._logger.info(f"Finishing balances: {padding}{balances_report(updated_balances)}")

    def _make_changes(self, balance_changes: typing.Sequence[InstrumentValue]) -> None:
        quote = self.quote_token.symbol
        for change in balance_changes:
            market_symbol = f"serum:{change.token.symbol}/{quote}"
            if change.value < 0:
                self.trade_executor.sell(market_symbol, change.value.copy_abs())
            else:
                self.trade_executor.buy(market_symbol, change.value.copy_abs())

    def _fetch_balances(self, context: Context, tokens: typing.Sequence[Token]) -> typing.Sequence[InstrumentValue]:
        balances: typing.List[InstrumentValue] = []
        for token in tokens:
            balance = InstrumentValue.fetch_total_value(context, self.wallet.address, token)
            balances += [balance]

        return balances


# # 🥭 LiveAccountBalancer class
#
# This is the high-level class that does much of the work.
#
class LiveAccountBalancer(WalletBalancer):
    def __init__(self, account: Account, group: Group, trade_executor: TradeExecutor,
                 targets: typing.Sequence[TargetBalance], action_threshold: Decimal) -> None:
        super().__init__()
        self.account: Account = account
        self.group: Group = group
        self.trade_executor: TradeExecutor = trade_executor
        self.targets: typing.Sequence[TargetBalance] = targets
        self.action_threshold: Decimal = action_threshold

    def balance(self, context: Context, prices: typing.Sequence[InstrumentValue]) -> None:
        padding = "\n    "

        def balances_report(balances: typing.Sequence[InstrumentValue]) -> str:
            return padding.join(list([f"{bal}" for bal in balances]))

        balances = [basket_token.net_value for basket_token in self.account.base_slots]
        total_value = Decimal(0)
        for bal in balances:
            price = InstrumentValue.find_by_token(prices, bal.token)
            value = bal.value * price.value
            total_value += value
        self._logger.info(f"Starting balances: {padding}{balances_report(balances)}")
        quote_token: Token = self.account.shared_quote_token
        total_token_value: InstrumentValue = InstrumentValue(quote_token, total_value)
        self._logger.info(f"Total: {total_token_value}")
        resolved_targets: typing.List[InstrumentValue] = []
        for target in self.targets:
            price = InstrumentValue.find_by_symbol(prices, target.symbol)
            resolved_targets += [target.resolve(price.token, price.value, total_value)]

        balance_changes = calculate_required_balance_changes(balances, resolved_targets)
        self._logger.info(f"Desired balance changes: {padding}{balances_report(balance_changes)}")

        dont_bother = FilterSmallChanges(self.action_threshold, balances, prices)
        filtered_changes = list(filter(dont_bother.allow, balance_changes))
        self._logger.info(f"Worthwhile balance changes: {padding}{balances_report(filtered_changes)}")
        if len(filtered_changes) == 0:
            self._logger.info("No balance changes to make.")
            return

        sorted_changes = sort_changes_for_trades(filtered_changes)
        self._make_changes(sorted_changes)

        updated_account: Account = Account.load(context, self.account.address, self.group)
        updated_balances = [basket_token.net_value for basket_token in updated_account.base_slots]
        self._logger.info(f"Finishing balances: {padding}{balances_report(updated_balances)}")

    def _make_changes(self, balance_changes: typing.Sequence[InstrumentValue]) -> None:
        quote = self.account.shared_quote_token.symbol
        for change in balance_changes:
            market_symbol = f"{change.token.symbol}/{quote}"
            if change.value < 0:
                self.trade_executor.sell(market_symbol, change.value.copy_abs())
            else:
                self.trade_executor.buy(market_symbol, change.value.copy_abs())
