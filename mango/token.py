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
import typing

from decimal import Decimal
from solana.publickey import PublicKey

from .constants import SOL_DECIMALS, SOL_MINT_ADDRESS


class Instrument:
    def __init__(self, symbol: str, name: str, decimals: Decimal) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.symbol: str = symbol.upper()
        self.name: str = name
        self.decimals: Decimal = decimals

    def round(self, value: Decimal) -> Decimal:
        return round(value, int(self.decimals))

    def shift_to_decimals(self, value: Decimal) -> Decimal:
        divisor = Decimal(10 ** self.decimals)
        shifted = value / divisor
        return shifted

    def shift_to_native(self, value: Decimal) -> Decimal:
        multiplier = Decimal(10 ** self.decimals)
        shifted = value * multiplier
        return round(shifted, 0)

    def symbol_matches(self, symbol: str) -> bool:
        return self.symbol.upper() == symbol.upper()

    # Instruments are equal if they have the same normalised symbol.
    def __eq__(self, other: typing.Any) -> bool:
        if isinstance(other, Instrument):
            return self.symbol == other.symbol
        return False

    def __str__(self) -> str:
        return f"« Instrument [{self.symbol}] '{self.name}' »"

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 Token class
#
# `Token` defines aspects common to every token.
#
class Token(Instrument):
    def __init__(self, symbol: str, name: str, decimals: Decimal, mint: PublicKey) -> None:
        super().__init__(symbol, name, decimals)
        self.mint: PublicKey = mint

    def ensure(uncertain_token: Instrument) -> "Token":
        if isinstance(uncertain_token, Token):
            return uncertain_token
        raise Exception(f"Instrument {uncertain_token} cannot be converted to SPL Token")

    @staticmethod
    def find_by_symbol(values: typing.Sequence["Token"], symbol: str) -> "Token":
        found = [value for value in values if value.symbol_matches(symbol)]
        if len(found) == 0:
            raise Exception(f"Token '{symbol}' not found in token values: {values}")

        if len(found) > 1:
            raise Exception(f"Token '{symbol}' matched multiple tokens in values: {values}")

        return found[0]

    @staticmethod
    def find_by_mint(values: typing.Sequence["Token"], mint: PublicKey) -> "Token":
        found = [value for value in values if value.mint == mint]
        if len(found) == 0:
            raise Exception(f"Token '{mint}' not found in token values: {values}")

        if len(found) > 1:
            raise Exception(f"Token '{mint}' matched multiple tokens in values: {values}")

        return found[0]

    # Tokens are equal if they have the same mint address.
    def __eq__(self, other: typing.Any) -> bool:
        if isinstance(other, Token):
            return self.mint == other.mint
        return False

    def __str__(self) -> str:
        return f"« Token [{self.symbol}] '{self.name}' [{self.mint} ({self.decimals} decimals)] »"


# # 🥭 SolToken object
#
# It's sometimes handy to have a `Token` for SOL, but SOL isn't actually a token and can't appear in baskets. This object defines a special case for SOL.
#
SolToken = Token("SOL", "Pure SOL", SOL_DECIMALS, SOL_MINT_ADDRESS)
