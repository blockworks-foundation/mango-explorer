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

from solana.publickey import PublicKey

from .accountinfo import AccountInfo


# # 🥭 AddressableAccount class
#
# Some of our most-used objects (like `Group` or `Account`) are accounts on Solana
# with packed data. When these are loaded, they're typically loaded by loading the
# `AccountInfo` and parsing it in an object-specific way.
#
# It's sometimes useful to be able to treat these in a common fashion so we use
# `AddressableAccount` as a way of sharing common features and providing a common base.
#
class AddressableAccount(metaclass=abc.ABCMeta):
    def __init__(self, account_info: AccountInfo) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.account_info = account_info

    @property
    def address(self) -> PublicKey:
        return self.account_info.address

    def __repr__(self) -> str:
        return f"{self}"
