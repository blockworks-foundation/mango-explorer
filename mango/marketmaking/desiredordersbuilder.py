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
import mango
import typing

from .modelstate import ModelState


# # 🥭 DesiredOrdersBuilder class
#
# A builder that builds a list of orders we'd like to be on the orderbook.
#
# The logic of what orders to create will be implemented in a derived class.
#

class DesiredOrdersBuilder(metaclass=abc.ABCMeta):
    def __init__(self):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def build(self, context: mango.Context, model_state: ModelState) -> typing.Sequence[mango.Order]:
        raise NotImplementedError("DesiredOrdersBuilder.build() is not implemented on the base type.")

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 NullDesiredOrdersBuilder class
#
# A no-op implementation of the `DesiredOrdersBuilder` that will never ask to create orders.
#

class NullDesiredOrdersBuilder(DesiredOrdersBuilder):
    def __init__(self):
        super().__init__()

    def build(self, context: mango.Context, model_state: ModelState) -> typing.Sequence[mango.Order]:
        return []

    def __str__(self) -> str:
        return "« 𝙽𝚞𝚕𝚕𝙳𝚎𝚜𝚒𝚛𝚎𝚍𝙾𝚛𝚍𝚎𝚛𝚜𝙱𝚞𝚒𝚕𝚍𝚎𝚛 »"
