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
import mango
import typing

from collections import deque

from .modelstate import ModelState


# # 🥭 OrderTracker class
#
# Maintains a history of orders that were placed (or at least an attempt was made).
#
class OrderTracker:
    def __init__(self, max_history: int = 20):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.tracked: typing.Deque[mango.Order] = deque(maxlen=max_history)

    def track(self, order: mango.Order):
        self.tracked += [order]

    def existing_orders(self, model_state: ModelState) -> typing.Sequence[mango.Order]:
        live_orders: typing.List[mango.Order] = []
        for existing_order in model_state.existing_orders:
            details = self._find_tracked(existing_order.client_id)
            if details is None:
                self.logger.warning(f"Could not find existing order with client ID {existing_order.client_id}")
                # Return a stub order so that the Reconciler has the chance to cancel it.
                stub = mango.Order.from_ids(existing_order.id, existing_order.client_id, existing_order.side)
                live_orders += [stub]
            else:
                if details.id != existing_order.id:
                    self.tracked.remove(details)
                    details = details.with_id(existing_order.id)
                    self.tracked += [details]

                live_orders += [details]

        return live_orders

    def _find_tracked(self, client_id_to_find: int) -> typing.Optional[mango.Order]:
        for tracked in self.tracked:
            if tracked.client_id == client_id_to_find:
                return tracked
        return None

    def __str__(self) -> str:
        return """« 𝙾𝚛𝚍𝚎𝚛𝚁𝚎𝚌𝚘𝚗𝚌𝚒𝚕𝚎𝚛 »"""

    def __repr__(self) -> str:
        return f"{self}"
