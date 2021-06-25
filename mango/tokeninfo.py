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

from .layouts import layouts
from .token import Token, TokenLookup

# # 🥭 TokenInfo class
#
# `TokenInfo` defines additional information for a `Token`.
#


class TokenInfo():
    def __init__(self, token: typing.Optional[Token], root_bank: PublicKey, decimals: Decimal):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.token: typing.Optional[Token] = token
        self.root_bank: PublicKey = root_bank
        self.decimals: Decimal = decimals

    def from_layout(layout: layouts.TOKEN_INFO, token_lookup: TokenLookup) -> "TokenInfo":
        token = token_lookup.find_by_mint(layout.mint)
        # TODO - this should be resolved. The decimals should match, but the mixture of token lookups is getting messy.
        # if token is not None:
        #     if layout.decimals != token.decimals:
        #         raise Exception(
        #             f"Conflict between number of decimals in token static data {token.decimals} and group {layout.decimals} for token {token.symbol}.")
        return TokenInfo(token, layout.root_bank, layout.decimals)

    def from_layout_or_none(layout: layouts.TOKEN_INFO, token_lookup: TokenLookup) -> typing.Optional["TokenInfo"]:
        if layout.mint is None:
            return None

        return TokenInfo.from_layout(layout, token_lookup)

    def __str__(self):
        return f"""« 𝚃𝚘𝚔𝚎𝚗𝙸𝚗𝚏𝚘 {self.token}
    Root Bank: {self.root_bank}
»"""

    def __repr__(self) -> str:
        return f"{self}"
