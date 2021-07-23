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
import enum
import logging
import typing

from solana.publickey import PublicKey

from .token import Token


class InventorySource(enum.Enum):
    SPL_TOKENS = enum.auto()
    ACCOUNT = enum.auto()

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 Market class
#
# This class describes a crypto market. It *must* have a base token and a quote token.
#

class Market(metaclass=abc.ABCMeta):
    def __init__(self, inventory_source: InventorySource, base: Token, quote: Token):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.inventory_source: InventorySource = inventory_source
        self.base: Token = base
        self.quote: Token = quote

    @property
    def symbol(self) -> str:
        return f"{self.base.symbol}/{self.quote.symbol}"

    @abc.abstractmethod
    def load(self, context: typing.Any) -> None:
        raise NotImplementedError("Market.load() is not implemented on the base type.")

    @abc.abstractmethod
    def ensure_loaded(self, context: typing.Any) -> None:
        raise NotImplementedError("Market.ensure_loaded() is not implemented on the base type.")

    def __str__(self) -> str:
        return f"« 𝙼𝚊𝚛𝚔𝚎𝚝 {self.symbol} »"

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 AddressableMarket class
#
# This class describes a crypto market. It *must* have a base token and a quote token.
#

class AddressableMarket(Market):
    def __init__(self, inventory_source: InventorySource, base: Token, quote: Token, address: PublicKey):
        super().__init__(inventory_source, base, quote)
        self.address: PublicKey = address

    def load(self, _: typing.Any) -> None:
        pass

    def ensure_loaded(self, _: typing.Any) -> None:
        pass

    def __str__(self) -> str:
        return f"« 𝙰𝚍𝚍𝚛𝚎𝚜𝚜𝚊𝚋𝚕𝚎𝙼𝚊𝚛𝚔𝚎𝚝 {self.symbol} [{self.address}] »"
