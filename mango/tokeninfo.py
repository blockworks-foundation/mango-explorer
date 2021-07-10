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

from .layouts import layouts
from .rootbank import RootBank
from .token import Token
from .tokenlookup import TokenLookup

# # 🥭 TokenInfo class
#
# `TokenInfo` defines additional information for a `Token`.
#


class TokenInfo():
    def __init__(self, token: Token, root_bank: RootBank, decimals: Decimal):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.token: Token = token
        self.root_bank: RootBank = root_bank
        self.decimals: Decimal = decimals

    def from_layout(layout: layouts.TOKEN_INFO, token_lookup: TokenLookup, root_banks: typing.Sequence[RootBank]) -> "TokenInfo":
        token = token_lookup.find_by_mint(layout.mint)
        if token is None:
            raise Exception(f"Token with mint {layout.mint} could not be found.")

        if layout.decimals != token.decimals:
            raise Exception(
                f"Conflict between number of decimals in token static data {token.decimals} and group {layout.decimals} for token {token.symbol}.")

        root_bank = RootBank.find_by_address(root_banks, layout.root_bank)
        return TokenInfo(token, root_bank, layout.decimals)

    def from_layout_or_none(layout: layouts.TOKEN_INFO, token_lookup: TokenLookup, root_banks: typing.Sequence[RootBank]) -> typing.Optional["TokenInfo"]:
        if layout.mint is None:
            return None

        return TokenInfo.from_layout(layout, token_lookup, root_banks)

    def __str__(self):
        root_bank = f"{self.root_bank}".replace("\n", "\n    ")
        return f"""« 𝚃𝚘𝚔𝚎𝚗𝙸𝚗𝚏𝚘 {self.token}
    {root_bank}
»"""

    def __repr__(self) -> str:
        return f"{self}"