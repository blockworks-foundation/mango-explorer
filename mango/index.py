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


import datetime
import logging
import typing

from decimal import Decimal

from .token import Token
from .tokenvalue import TokenValue
from .version import Version


# # 🥭 Index class
#
class Index:
    def __init__(self, version: Version, token: Token, last_update: datetime.datetime, borrow: TokenValue, deposit: TokenValue):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.version: Version = version
        self.token: Token = token
        self.last_update: datetime.datetime = last_update
        self.borrow: TokenValue = borrow
        self.deposit: TokenValue = deposit

    @staticmethod
    def from_layout(layout: typing.Any, token: Token) -> "Index":
        borrow = TokenValue(token, layout.borrow / Decimal(10 ** token.decimals))
        deposit = TokenValue(token, layout.deposit / Decimal(10 ** token.decimals))
        return Index(Version.UNSPECIFIED, token, layout.last_update, borrow, deposit)

    def __str__(self) -> str:
        return f"""« Index [{self.token.symbol}] ({self.last_update}):
    Borrow: {self.borrow},
    Deposit: {self.deposit} »"""

    def __repr__(self) -> str:
        return f"{self}"
