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

from solana.publickey import PublicKey

from .index import Index
from .token import Token


# # 🥭 BasketToken class
#
# `BasketToken` defines aspects of `Token`s that are part of a `Group` basket.
#


class BasketToken:
    def __init__(self, token: Token, vault: PublicKey, index: Index):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.token: Token = token
        self.vault: PublicKey = vault
        self.index: Index = index

    @staticmethod
    def find_by_symbol(values: typing.List["BasketToken"], symbol: str) -> "BasketToken":
        found = [value for value in values if value.token.symbol_matches(symbol)]
        if len(found) == 0:
            raise Exception(f"Token '{symbol}' not found in token values: {values}")

        if len(found) > 1:
            raise Exception(f"Token '{symbol}' matched multiple tokens in values: {values}")

        return found[0]

    @staticmethod
    def find_by_mint(values: typing.List["BasketToken"], mint: PublicKey) -> "BasketToken":
        found = [value for value in values if value.token.mint == mint]
        if len(found) == 0:
            raise Exception(f"Token '{mint}' not found in token values: {values}")

        if len(found) > 1:
            raise Exception(f"Token '{mint}' matched multiple tokens in values: {values}")

        return found[0]

    @staticmethod
    def find_by_token(values: typing.List["BasketToken"], token: Token) -> "BasketToken":
        return BasketToken.find_by_mint(values, token.mint)

    # BasketTokens are equal if they have the same underlying token.
    def __eq__(self, other):
        if hasattr(other, 'token'):
            return self.token == other.token
        return False

    def __str__(self) -> str:
        index = str(self.index).replace("\n", "\n    ")
        return f"""« BasketToken:
    {self.token}
    Vault: {self.vault}
    Index: {index}
»"""

    def __repr__(self) -> str:
        return f"{self}"
