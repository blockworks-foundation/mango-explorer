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

from .token import Token

# # 🥭 BalanceSheet class
#


class BalanceSheet:
    def __init__(self, token: Token, liabilities: Decimal, settled_assets: Decimal, unsettled_assets: Decimal):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.token: Token = token
        self.liabilities: Decimal = liabilities
        self.settled_assets: Decimal = settled_assets
        self.unsettled_assets: Decimal = unsettled_assets

    @property
    def assets(self) -> Decimal:
        return self.settled_assets + self.unsettled_assets

    @property
    def value(self) -> Decimal:
        return self.assets - self.liabilities

    @property
    def collateral_ratio(self) -> Decimal:
        if self.liabilities == Decimal(0):
            return Decimal(0)
        return self.assets / self.liabilities

    @staticmethod
    def report(values: typing.Sequence["BalanceSheet"], reporter: typing.Callable[[str], None] = print) -> None:
        for value in values:
            reporter(str(value))

    def __str__(self) -> str:
        name = "«𝚄𝚗𝚜𝚙𝚎𝚌𝚒𝚏𝚒𝚎𝚍»"
        if self.token is not None:
            name = self.token.name

        return f"""« 𝙱𝚊𝚕𝚊𝚗𝚌𝚎𝚂𝚑𝚎𝚎𝚝 [{name}]:
    Assets :           {self.assets:>18,.8f}
    Settled Assets :   {self.settled_assets:>18,.8f}
    Unsettled Assets : {self.unsettled_assets:>18,.8f}
    Liabilities :      {self.liabilities:>18,.8f}
    Value :            {self.value:>18,.8f}
    Collateral Ratio : {self.collateral_ratio:>18,.2%}
»
"""

    def __repr__(self) -> str:
        return f"{self}"
