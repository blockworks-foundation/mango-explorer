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
from .layouts import layouts


# # 🥭 MangoAccountFlags class
#
# The Mango prefix is because there's also `SerumAccountFlags` for the standard Serum flags.
#

class MangoAccountFlags:
    def __init__(self, version: Version, initialized: bool, group: bool, margin_account: bool, srm_account: bool):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.version: Version = version
        self.initialized = initialized
        self.group = group
        self.margin_account = margin_account
        self.srm_account = srm_account

    @staticmethod
    def from_layout(layout: layouts.MANGO_ACCOUNT_FLAGS) -> "MangoAccountFlags":
        return MangoAccountFlags(Version.UNSPECIFIED, layout.initialized, layout.group,
                                 layout.margin_account, layout.srm_account)

    def __str__(self) -> str:
        flags: typing.List[typing.Optional[str]] = []
        flags += ["initialized" if self.initialized else None]
        flags += ["group" if self.group else None]
        flags += ["margin_account" if self.margin_account else None]
        flags += ["srm_account" if self.srm_account else None]
        flag_text = " | ".join(flag for flag in flags if flag is not None) or "None"
        return f"« MangoAccountFlags: {flag_text} »"

    def __repr__(self) -> str:
        return f"{self}"
