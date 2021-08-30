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

from .market import Market


# # 🥭 MarketLookup class
#
# This base class allows specialised ways of looking up markets by symbol or by address.
#

class MarketLookup(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def find_by_symbol(self, symbol: str) -> typing.Optional[Market]:
        raise NotImplementedError("MarketLookup.find_by_symbol() is not implemented on the base type.")

    @abc.abstractmethod
    def find_by_address(self, address: PublicKey) -> typing.Optional[Market]:
        raise NotImplementedError("MarketLookup.find_by_address() is not implemented on the base type.")

    @abc.abstractmethod
    def all_markets(self) -> typing.Sequence[Market]:
        raise NotImplementedError("MarketLookup.all_markets() is not implemented on the base type.")


# # 🥭 NullMarketLookup class
#
# This class is a simple stub `MarketLookup` that never returns a `Market`.
#

class NullMarketLookup(MarketLookup):
    def __init__(self) -> None:
        super().__init__()

    def find_by_symbol(self, symbol: str) -> typing.Optional[Market]:
        return None

    def find_by_address(self, address: PublicKey) -> typing.Optional[Market]:
        return None

    def all_markets(self) -> typing.Sequence[Market]:
        return []


# # 🥭 CompoundMarketLookup class
#
# This class allows multiple `MarketLookup` objects to be combined, returning the first valid lookup result
# found.
#

class CompoundMarketLookup(MarketLookup):
    def __init__(self, lookups: typing.Sequence[MarketLookup]) -> None:
        super().__init__()
        self.lookups: typing.Sequence[MarketLookup] = lookups

    def find_by_symbol(self, symbol: str) -> typing.Optional[Market]:
        for lookup in self.lookups:
            result = lookup.find_by_symbol(symbol)
            if result is not None:
                return result
        return None

    def find_by_address(self, address: PublicKey) -> typing.Optional[Market]:
        for lookup in self.lookups:
            result = lookup.find_by_address(address)
            if result is not None:
                return result
        return None

    def all_markets(self) -> typing.Sequence[Market]:
        return [market for sublist in map(lambda lookup: lookup.all_markets(), self.lookups) for market in sublist]
