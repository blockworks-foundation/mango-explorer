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


# # 🥭 Metadata class
#
class Metadata():
    def __init__(self, data_type: typing.Any, version: Version, is_initialized: bool):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.data_type: typing.Any = data_type
        self.version: Version = version
        self.is_initialized: bool = is_initialized

    def from_layout(layout: typing.Any) -> "Metadata":
        version = Version(layout.version + 1)
        is_initialized = bool(layout.is_initialized)
        return Metadata(layout.data_type, version, is_initialized)

    def __str__(self) -> str:
        init = "Initialized" if self.is_initialized else "Not Initialized"
        return f"« 𝙼𝚎𝚝𝚊𝚍𝚊𝚝𝚊 {self.version} - {self.data_type}: {init} »"

    def __repr__(self) -> str:
        return f"{self}"
