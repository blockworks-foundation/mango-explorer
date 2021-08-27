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

from .version import Version


# # 🥭 AccountFlags class
#
# Encapsulates the Serum AccountFlags data.
#

class AccountFlags:
    def __init__(self, version: Version, initialized: bool, market: bool, open_orders: bool,
                 request_queue: bool, event_queue: bool, bids: bool, asks: bool, disabled: bool):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.version: Version = version
        self.initialized: bool = initialized
        self.market: bool = market
        self.open_orders: bool = open_orders
        self.request_queue: bool = request_queue
        self.event_queue: bool = event_queue
        self.bids: bool = bids
        self.asks: bool = asks
        self.disabled: bool = disabled

    @staticmethod
    def from_layout(layout: typing.Any) -> "AccountFlags":
        return AccountFlags(Version.UNSPECIFIED, layout.initialized, layout.market,
                            layout.open_orders, layout.request_queue, layout.event_queue,
                            layout.bids, layout.asks, layout.disabled)

    def __str__(self) -> str:
        flags: typing.List[typing.Optional[str]] = []
        flags += ["initialized" if self.initialized else None]
        flags += ["market" if self.market else None]
        flags += ["open_orders" if self.open_orders else None]
        flags += ["request_queue" if self.request_queue else None]
        flags += ["event_queue" if self.event_queue else None]
        flags += ["bids" if self.bids else None]
        flags += ["asks" if self.asks else None]
        flags += ["disabled" if self.disabled else None]
        flag_text = " | ".join(flag for flag in flags if flag is not None) or "None"
        return f"« 𝙰𝚌𝚌𝚘𝚞𝚗𝚝𝙵𝚕𝚊𝚐𝚜: {flag_text} »"

    def __repr__(self) -> str:
        return f"{self}"
