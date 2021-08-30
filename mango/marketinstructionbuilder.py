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

from decimal import Decimal
from solana.publickey import PublicKey

from .combinableinstructions import CombinableInstructions
from .orders import Order


# # 🥭 MarketInstructionBuilder class
#
# This abstracts the process of buiding instructions for placing orders and cancelling orders.
#
# It's abstracted because we may want to have different implementations for different market types.
#
# Whichever choice is made, the calling code shouldn't have to care. It should be able to
# use its `MarketInstructionBuilder` class as simply as:
# ```
# instruction_builder.build_cancel_order_instructions(order)
# ```
#
# As a matter of policy for all InstructionBuidlers, construction and build_* methods should all work with
# existing data, requiring no fetches from Solana or other sources. All necessary data should all be loaded
# on initial setup in the `load()` method.
#

class MarketInstructionBuilder(metaclass=abc.ABCMeta):
    def __init__(self):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def build_cancel_order_instructions(self, order: Order, ok_if_missing: bool = False) -> CombinableInstructions:
        raise NotImplementedError(
            "MarketInstructionBuilder.build_cancel_order_instructions() is not implemented on the base type.")

    @abc.abstractmethod
    def build_place_order_instructions(self, order: Order) -> CombinableInstructions:
        raise NotImplementedError(
            "MarketInstructionBuilder.build_place_order_instructions() is not implemented on the base type.")

    @abc.abstractmethod
    def build_settle_instructions(self) -> CombinableInstructions:
        raise NotImplementedError(
            "MarketInstructionBuilder.build_settle_instructions() is not implemented on the base type.")

    @abc.abstractmethod
    def build_crank_instructions(self, open_orders_addresses: typing.Sequence[PublicKey], limit: Decimal = Decimal(32)) -> CombinableInstructions:
        raise NotImplementedError(
            "MarketInstructionBuilder.build_crank_instructions() is not implemented on the base type.")

    @abc.abstractmethod
    def build_redeem_instructions(self) -> CombinableInstructions:
        raise NotImplementedError(
            "MarketInstructionBuilder.build_redeem_instructions() is not implemented on the base type.")

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 NullMarketInstructionBuilder class
#
# A null, no-op, dry-run trade executor that can be plugged in anywhere a `MarketInstructionBuilder`
# is expected, but which will not actually trade.
#

class NullMarketInstructionBuilder(MarketInstructionBuilder):
    def __init__(self, symbol: str):
        super().__init__()
        self.symbol: str = symbol

    def build_cancel_order_instructions(self, order: Order, ok_if_missing: bool = False) -> CombinableInstructions:
        return CombinableInstructions.empty()

    def build_place_order_instructions(self, order: Order) -> CombinableInstructions:
        return CombinableInstructions.empty()

    def build_settle_instructions(self) -> CombinableInstructions:
        return CombinableInstructions.empty()

    def build_crank_instructions(self, addresses_to_crank: typing.Sequence[PublicKey], limit: Decimal = Decimal(32)) -> CombinableInstructions:
        return CombinableInstructions.empty()

    def build_redeem_instructions(self) -> CombinableInstructions:
        return CombinableInstructions.empty()

    def __str__(self) -> str:
        return f"« 𝙽𝚞𝚕𝚕𝙼𝚊𝚛𝚔𝚎𝚝𝙸𝚗𝚜𝚝𝚛𝚞𝚌𝚝𝚒𝚘𝚗𝙱𝚞𝚒𝚕𝚍𝚎𝚛 {self.symbol} »"
