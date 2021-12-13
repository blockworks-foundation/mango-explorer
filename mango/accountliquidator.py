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

from solana.transaction import TransactionInstruction

from .liquidatablereport import LiquidatableReport


# # 🥭 AccountLiquidator
#
# An `AccountLiquidator` liquidates an `Account`, if possible.
#
# The follows the common pattern of having an abstract base class that defines the interface
# external code should use, along with a 'null' implementation and at least one full
# implementation.
#
# The idea is that preparing code can choose whether to use the null implementation (in the
# case of a 'dry run' for instance) or the full implementation, but the code that defines
# the algorithm - which actually calls the `AccountLiquidator` - doesn't have to care about
# this choice.
#

# # 💧 AccountLiquidator class
#
# This abstract base class defines the interface to account liquidators, which in this case
# is just the `liquidate()` method.
#

class AccountLiquidator(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def prepare_instructions(self, liquidatable_report: LiquidatableReport) -> typing.Sequence[TransactionInstruction]:
        raise NotImplementedError("AccountLiquidator.prepare_instructions() is not implemented on the base type.")

    @abc.abstractmethod
    def liquidate(self, liquidatable_report: LiquidatableReport) -> typing.Optional[typing.Sequence[str]]:
        raise NotImplementedError("AccountLiquidator.liquidate() is not implemented on the base type.")


# # NullAccountLiquidator class
#
# A 'null', 'no-op', 'dry run' implementation of the `AccountLiquidator` class.
#

class NullAccountLiquidator(AccountLiquidator):
    def __init__(self) -> None:
        super().__init__()

    def prepare_instructions(self, liquidatable_report: LiquidatableReport) -> typing.Sequence[TransactionInstruction]:
        return []

    def liquidate(self, liquidatable_report: LiquidatableReport) -> typing.Optional[typing.Sequence[str]]:
        self._logger.info(f"Skipping liquidation of account [{liquidatable_report.account.address}]")
        return None
