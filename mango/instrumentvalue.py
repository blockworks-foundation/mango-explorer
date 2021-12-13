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
import numbers
import typing

from decimal import Decimal
from solana.publickey import PublicKey
from solana.rpc.types import TokenAccountOpts

from .context import Context
from .token import Instrument, Token


def _decimal_from_number(value: numbers.Number) -> Decimal:
    # Decimal constructor can only handle these Number types:
    # Union[Decimal, float, str, Tuple[int, Sequence[int], int]]
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(value)
    if isinstance(value, str):
        return Decimal(value)
    raise Exception(f"Cannot handle conversion of {value} to Decimal.")


# # 🥭 InstrumentValue class
#
# The `InstrumentValue` class is a simple way of keeping a token and value together, and
# displaying them nicely consistently.
#
class InstrumentValue:
    def __init__(self, token: Instrument, value: Decimal) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.token: Instrument = token
        self.value: Decimal = value
        if not isinstance(self.value, Decimal):
            raise Exception(f"Value is {type(self.value)}, not Decimal: {self.value}")

    def shift_to_native(self) -> "InstrumentValue":
        new_value = self.token.shift_to_native(self.value)
        return InstrumentValue(self.token, new_value)

    @staticmethod
    def fetch_total_value_or_none(context: Context, account_public_key: PublicKey, token: Token) -> typing.Optional["InstrumentValue"]:
        opts = TokenAccountOpts(mint=token.mint)

        token_accounts = context.client.get_token_accounts_by_owner(account_public_key, opts)
        if len(token_accounts) == 0:
            return None

        total_value = Decimal(0)
        for token_account in token_accounts:
            token_balance: Decimal = context.client.get_token_account_balance(token_account["pubkey"])
            total_value += token_balance

        return InstrumentValue(token, total_value)

    @staticmethod
    def fetch_total_value(context: Context, account_public_key: PublicKey, token: Token) -> "InstrumentValue":
        value = InstrumentValue.fetch_total_value_or_none(context, account_public_key, token)
        if value is None:
            return InstrumentValue(token, Decimal(0))
        return value

    @staticmethod
    def report(values: typing.Sequence["InstrumentValue"], reporter: typing.Callable[[str], None] = print) -> None:
        for value in values:
            reporter(f"{value.value:>18,.8f} {value.token.name}")

    @staticmethod
    def find_by_symbol(values: typing.Sequence[typing.Optional["InstrumentValue"]], symbol: str) -> "InstrumentValue":
        found = [
            value for value in values if value is not None and value.token is not None and value.token.symbol_matches(symbol)]
        if len(found) == 0:
            raise Exception(f"Token '{symbol}' not found in token values: {values}")

        if len(found) > 1:
            raise Exception(f"Token '{symbol}' matched multiple tokens in values: {values}")

        return found[0]

    @staticmethod
    def find_by_token(values: typing.Sequence[typing.Optional["InstrumentValue"]], token: Instrument) -> "InstrumentValue":
        return InstrumentValue.find_by_symbol(values, token.symbol)

    @staticmethod
    def changes(before: typing.Sequence["InstrumentValue"], after: typing.Sequence["InstrumentValue"]) -> typing.Sequence["InstrumentValue"]:
        changes: typing.List[InstrumentValue] = []
        for before_balance in before:
            after_balance = InstrumentValue.find_by_token(after, before_balance.token)
            result = InstrumentValue(before_balance.token, after_balance.value - before_balance.value)
            changes += [result]

        return changes

    def __add__(self, token_value_to_add: "InstrumentValue") -> "InstrumentValue":
        if self.token != token_value_to_add.token:
            raise Exception(
                f"Cannot add InstrumentValues from different tokens ({self.token} and {token_value_to_add.token}).")
        return InstrumentValue(self.token, self.value + token_value_to_add.value)

    def __sub__(self, token_value_to_subtract: "InstrumentValue") -> "InstrumentValue":
        if self.token != token_value_to_subtract.token:
            raise Exception(
                f"Cannot subtract InstrumentValues from different tokens ({self.token} and {token_value_to_subtract.token}).")
        return InstrumentValue(self.token, self.value - token_value_to_subtract.value)

    def __mul__(self, token_value_to_multiply: "InstrumentValue") -> "InstrumentValue":
        # Multiplying by another InstrumentValue is assumed to be a token value multiplied by a token price.
        # The result should be denominated in the currency of the price.
        return InstrumentValue(token_value_to_multiply.token, self.value * token_value_to_multiply.value)

    def __lt__(self, other: typing.Any) -> bool:
        if isinstance(other, numbers.Number):
            return self.value < _decimal_from_number(other)

        if not isinstance(other, InstrumentValue):
            return NotImplemented

        if self.token != other.token:
            raise Exception(
                f"Cannot compare token values when one token is {self.token.symbol} and the other is {other.token.symbol}.")
        return self.value < other.value

    def __gt__(self, other: typing.Any) -> bool:
        if isinstance(other, numbers.Number):
            return self.value > _decimal_from_number(other)

        if not isinstance(other, InstrumentValue):
            return NotImplemented

        if self.token != other.token:
            raise Exception(
                f"Cannot compare token values when one token is {self.token.symbol} and the other is {other.token.symbol}.")
        return self.value > other.value

    def __eq__(self, other: typing.Any) -> bool:
        if isinstance(other, InstrumentValue) and self.token == other.token and self.value == other.value:
            return True
        return False

    def __format__(self, format_spec: str) -> str:
        return format(str(self), format_spec)

    def __str__(self) -> str:
        name = "« Un-Named Instrument »"
        if self.token and self.token.name:
            name = self.token.name
        return f"« InstrumentValue: {self.value:>18,.8f} {name} »"

    def __repr__(self) -> str:
        return f"{self}"
