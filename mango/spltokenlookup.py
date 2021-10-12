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

import json
import logging
import os.path
import typing

from decimal import Decimal
from solana.publickey import PublicKey

from .constants import DATA_PATH
from .token import Token
from .tokenlookup import TokenLookup


# # 🥭 SplTokenLookup class
#
# This class allows us to look up token data specifically from Solana static data.
#
# The Solana static data is the [Solana token list](https://raw.githubusercontent.com/solana-labs/token-list/main/src/tokens/solana.tokenlist.json) provided by Serum.
#
# You can load an `SplTokenLookup` class by something like:
# ```
# with open("solana.tokenlist.json") as json_file:
#     token_data = json.load(json_file)
#     token_lookup = TokenLookup(token_data)
# ```
#

class SplTokenLookup(TokenLookup):
    DefaultDataFilepath = os.path.join(DATA_PATH, "solana.tokenlist.json")

    def __init__(self, filename: str, token_data: typing.Dict) -> None:
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.filename: str = filename
        self.token_data = token_data

    def find_by_symbol(self, symbol: str) -> typing.Optional[Token]:
        for token in self.token_data["tokens"]:
            if token["symbol"] == symbol:
                return Token(token["symbol"], token["name"], PublicKey(token["address"]), Decimal(token["decimals"]))

        return None

    def find_by_mint(self, mint: PublicKey) -> typing.Optional[Token]:
        mint_string: str = str(mint)
        for token in self.token_data["tokens"]:
            if token["address"] == mint_string:
                return Token(token["symbol"], token["name"], PublicKey(token["address"]), Decimal(token["decimals"]))

        return None

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

    @staticmethod
    def load(filename: str) -> "TokenLookup":
        with open(filename, encoding='utf-8') as json_file:
            token_data = json.load(json_file)
            return SplTokenLookup(filename, token_data)

    def __str__(self) -> str:
        return f"« 𝚂𝚙𝚕𝚃𝚘𝚔𝚎𝚗𝙻𝚘𝚘𝚔𝚞𝚙 [{self.filename}] »"
