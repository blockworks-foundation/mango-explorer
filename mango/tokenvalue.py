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
from .token import Token


# # 🥭 TokenValue class
#
# The `TokenValue` class is a simple way of keeping a token and value together, and
# displaying them nicely consistently.
#

class TokenValue:
    def __init__(self, token: Token, value: Decimal):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.token = token
        self.value = value
        if not isinstance(self.value, Decimal):
            raise Exception(f"Value is {type(self.value)}, not Decimal: {self.value}")

    def shift_to_native(self) -> "TokenValue":
        new_value = self.token.shift_to_native(self.value)
        return TokenValue(self.token, new_value)

    @staticmethod
    def fetch_total_value_or_none(context: Context, account_public_key: PublicKey, token: Token) -> typing.Optional["TokenValue"]:
        opts = TokenAccountOpts(mint=token.mint)

        token_accounts = context.client.get_token_accounts_by_owner(account_public_key, opts)
        if len(token_accounts) == 0:
            return None

        total_value = Decimal(0)
        for token_account in token_accounts:
            token_balance: Decimal = context.client.get_token_account_balance(token_account["pubkey"])
            total_value += token_balance

        return TokenValue(token, total_value)

    @staticmethod
    def fetch_total_value(context: Context, account_public_key: PublicKey, token: Token) -> "TokenValue":
        value = TokenValue.fetch_total_value_or_none(context, account_public_key, token)
        if value is None:
            return TokenValue(token, Decimal(0))
        return value

    @staticmethod
    def report(values: typing.Sequence["TokenValue"], reporter: typing.Callable[[str], None] = print) -> None:
        for value in values:
            reporter(f"{value.value:>18,.8f} {value.token.name}")

    @staticmethod
    def find_by_symbol(values: typing.Sequence[typing.Optional["TokenValue"]], symbol: str) -> "TokenValue":
        found = [
            value for value in values if value is not None and value.token is not None and value.token.symbol_matches(symbol)]
        if len(found) == 0:
            raise Exception(f"Token '{symbol}' not found in token values: {values}")

        if len(found) > 1:
            raise Exception(f"Token '{symbol}' matched multiple tokens in values: {values}")

        return found[0]

    @staticmethod
    def find_by_mint(values: typing.Sequence[typing.Optional["TokenValue"]], mint: PublicKey) -> "TokenValue":
        found = [value for value in values if value is not None and value.token is not None and value.token.mint == mint]
        if len(found) == 0:
            raise Exception(f"Token '{mint}' not found in token values: {values}")

        if len(found) > 1:
            raise Exception(f"Token '{mint}' matched multiple tokens in values: {values}")

        return found[0]

    @staticmethod
    def find_by_token(values: typing.Sequence[typing.Optional["TokenValue"]], token: Token) -> "TokenValue":
        return TokenValue.find_by_mint(values, token.mint)

    @staticmethod
    def changes(before: typing.Sequence["TokenValue"], after: typing.Sequence["TokenValue"]) -> typing.Sequence["TokenValue"]:
        changes: typing.List[TokenValue] = []
        for before_balance in before:
            after_balance = TokenValue.find_by_token(after, before_balance.token)
            result = TokenValue(before_balance.token, after_balance.value - before_balance.value)
            changes += [result]

        return changes

    def __add__(self, token_value_to_add: "TokenValue") -> "TokenValue":
        if self.token != token_value_to_add.token:
            raise Exception(
                f"Cannot add TokenValues from different tokens ({self.token} and {token_value_to_add.token}).")
        return TokenValue(self.token, self.value + token_value_to_add.value)

    def __sub__(self, token_value_to_subtract: "TokenValue") -> "TokenValue":
        if self.token != token_value_to_subtract.token:
            raise Exception(
                f"Cannot subtract TokenValues from different tokens ({self.token} and {token_value_to_subtract.token}).")
        return TokenValue(self.token, self.value - token_value_to_subtract.value)

    def __mul__(self, token_value_to_multiply: "TokenValue") -> "TokenValue":
        # Multiplying by another TokenValue is assumed to be a token value multiplied by a token price.
        # The result should be denominated in the currency of the price.
        return TokenValue(token_value_to_multiply.token, self.value * token_value_to_multiply.value)

    def __lt__(self, other):
        if isinstance(other, numbers.Number):
            return self.value < other

        if not isinstance(other, TokenValue):
            return NotImplemented

        if self.token != other.token:
            raise Exception(
                f"Cannot compare token values when one token is {self.token.symbol} and the other is {other.token.symbol}.")
        return self.value < other.value

    def __gt__(self, other):
        if isinstance(other, numbers.Number):
            return self.value > other

        if not isinstance(other, TokenValue):
            return NotImplemented

        if self.token != other.token:
            raise Exception(
                f"Cannot compare token values when one token is {self.token.symbol} and the other is {other.token.symbol}.")
        return self.value > other.value

    def __eq__(self, other: typing.Any) -> bool:
        if isinstance(other, TokenValue) and self.token == other.token and self.value == other.value:
            return True
        return False

    def __format__(self, format_spec):
        return format(str(self), format_spec)

    def __str__(self) -> str:
        name = "« 𝚄𝚗-𝙽𝚊𝚖𝚎𝚍 𝚃𝚘𝚔𝚎𝚗 »"
        if self.token and self.token.name:
            name = self.token.name
        return f"« 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎: {self.value:>18,.8f} {name} »"

    def __repr__(self) -> str:
        return f"{self}"
