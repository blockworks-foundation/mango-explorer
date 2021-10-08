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
import argparse
import logging
import mango
import typing

from ...modelstate import ModelState


# # 🥭 Element class
#
# A base class for a part of a chain that can take in a sequence of elements and process them, changing
# them as desired.
#
# Only `Order`s returned from `process()` method are passed to the next element of the chain.
#
class Element(metaclass=abc.ABCMeta):
    def __init__(self):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        pass

    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> "Element":
        raise NotImplementedError("Element.from_command_line_parameters() is not implemented on the base type.")

    @abc.abstractmethod
    def process(self, context: mango.Context, model_state: ModelState, orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        raise NotImplementedError("Element.process() is not implemented on the base type.")

    def __repr__(self) -> str:
        return f"{self}"

    def __str__(self) -> str:
        return """« 𝙴𝚕𝚎𝚖𝚎𝚗𝚝 »"""
