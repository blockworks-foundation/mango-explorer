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

from decimal import Decimal

from .layouts import layouts
from .version import Version


# # 🥭 Index class
#


class Index:
    def __init__(self, version: Version, last_update: datetime.datetime, borrow: Decimal, deposit: Decimal):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.version: Version = version
        self.last_update: datetime.datetime = last_update
        self.borrow: Decimal = borrow
        self.deposit: Decimal = deposit

    @staticmethod
    def from_layout(layout: layouts.INDEX, decimals: Decimal) -> "Index":
        borrow = layout.borrow / Decimal(10 ** decimals)
        deposit = layout.deposit / Decimal(10 ** decimals)
        return Index(Version.UNSPECIFIED, layout.last_update, borrow, deposit)

    def __str__(self) -> str:
        return f"« Index [{self.last_update}]: Borrow: {self.borrow:,.8f}, Deposit: {self.deposit:,.8f} »"

    def __repr__(self) -> str:
        return f"{self}"
