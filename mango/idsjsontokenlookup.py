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

import typing

from decimal import Decimal
from solana.publickey import PublicKey

from .constants import MangoConstants
from .token import Token
from .tokenlookup import TokenLookup


# # 🥭 IdsJsonTokenLookup class
#
# This class allows us to look up token data from our ids.json configuration file.
#

class IdsJsonTokenLookup(TokenLookup):
    def __init__(self, cluster_name: str, group_name: str) -> None:
        super().__init__()
        self.cluster_name: str = cluster_name
        self.group_name: str = group_name

    def find_by_symbol(self, symbol: str) -> typing.Optional[Token]:
        for group in MangoConstants["groups"]:
            if group["cluster"] == self.cluster_name and group["name"] == self.group_name:
                for token in group["tokens"]:
                    if token["symbol"] == symbol:
                        return Token(token["symbol"], token["symbol"], PublicKey(token["mintKey"]), Decimal(token["decimals"]))
        return None

    def find_by_mint(self, mint: PublicKey) -> typing.Optional[Token]:
        mint_str = str(mint)
        for group in MangoConstants["groups"]:
            if group["cluster"] == self.cluster_name and group["name"] == self.group_name:
                for token in group["tokens"]:
                    if token["mintKey"] == mint_str:
                        return Token(token["symbol"], token["symbol"], PublicKey(token["mintKey"]), Decimal(token["decimals"]))
        return None

    def __str__(self) -> str:
        return f"« 𝙸𝚍𝚜𝙹𝚜𝚘𝚗𝚃𝚘𝚔𝚎𝚗𝙻𝚘𝚘𝚔𝚞𝚙 [{self.cluster_name}, {self.group_name}] »"
