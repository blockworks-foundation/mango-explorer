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

from ..modelstate import ModelState
from .reconciledorders import ReconciledOrders


# # 🥭 OrderReconciler class
#
# Base class for order reconciler that combines existing and desired orders into buckets inside a `ReconciledOrders`.
#
class OrderReconciler(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def reconcile(self, model_state: ModelState, existing_orders: typing.Sequence[mango.Order], desired_orders: typing.Sequence[mango.Order]) -> ReconciledOrders:
        raise NotImplementedError("OrderReconciler.reconcile() is not implemented on the base type.")

    def __str__(self) -> str:
        return """« OrderReconciler »"""

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 NullOrderReconciler class
#
# Null implementation of OrderReconciler. Just maintains all existing orders.
#
class NullOrderReconciler(OrderReconciler):
    def __init__(self) -> None:
        super().__init__()

    def reconcile(self, _: ModelState, existing_orders: typing.Sequence[mango.Order], desired_orders: typing.Sequence[mango.Order]) -> ReconciledOrders:
        outcomes: ReconciledOrders = ReconciledOrders()
        outcomes.to_keep = list(existing_orders)
        outcomes.to_ignore = list(desired_orders)
        return outcomes

    def __str__(self) -> str:
        return """« NullOrderReconciler »"""
