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

from solana.publickey import PublicKey

from .token import Token


# # 🥭 TokenLookup class
#
# This class allows us to look up token symbols, names, mint addresses and decimals, all from our Mango
# and Solana static data.
#
# It's usually easiest to access it via the `Context` as `context.token_lookup`.
#


class TokenLookup(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def find_by_symbol(self, symbol: str) -> typing.Optional[Token]:
        raise NotImplementedError("TokenLookup.find_by_symbol() is not implemented on the base type.")

    @abc.abstractmethod
    def find_by_mint(self, mint: PublicKey) -> typing.Optional[Token]:
        raise NotImplementedError("TokenLookup.find_by_mint() is not implemented on the base type.")

    def find_by_symbol_or_raise(self, symbol: str) -> Token:
        token = self.find_by_symbol(symbol)
        if token is None:
            raise Exception(f"Could not find token with symbol '{symbol}'.")

        return token

    def find_by_mint_or_raise(self, mint: PublicKey) -> Token:
        token = self.find_by_mint(mint)
        if token is None:
            raise Exception(f"Could not find token with mint {mint}.")

        return token


# # 🥭 CompoundTokenLookup class
#
# This class allows multiple `TokenLookup` objects to be combined, returning the first valid lookup result
# found.
#

class CompoundTokenLookup(TokenLookup):
    def __init__(self, lookups: typing.Sequence[TokenLookup]) -> None:
        super().__init__()
        self.lookups: typing.Sequence[TokenLookup] = lookups

    def find_by_symbol(self, symbol: str) -> typing.Optional[Token]:
        for lookup in self.lookups:
            result = lookup.find_by_symbol(symbol)
            if result is not None:
                return result
        return None

    def find_by_mint(self, mint: PublicKey) -> typing.Optional[Token]:
        for lookup in self.lookups:
            result = lookup.find_by_mint(mint)
            if result is not None:
                return result
        return None
