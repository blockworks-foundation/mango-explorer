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


import typing


# # 🥭 TWatched generic type
#
# Just a generic type name for watchers.
#
TWatched = typing.TypeVar("TWatched", covariant=True)


# # 🥭 Watcher protocol
#
# The `Watcher` protocol just says the object has a property `latest` of type `TWatched`.
#
# The idea behind this is that we can have an object that's subscribed to a websocket and updates, say,
# the Group. But instead of having to explicitly reference websocket implementation details or force
# a common base class on all watchers, we can use the protocol to have any object be a `Watcher` as long
# as it provides a `latest` property of the appropriate type.
#
class Watcher(typing.Protocol[TWatched]):
    @property
    def latest(self) -> TWatched:
        raise NotImplementedError("Watcher.latest is not implemented on the Protocol.")


# # 🥭 ManualUpdateWatcher class
#
# The `ManualUpdateWatcher` class provides a basic implementation of the `Watcher` protocol that
# requires manual intervention (updating of the `value` member) to set the latest version.
#
class ManualUpdateWatcher(typing.Generic[TWatched]):
    def __init__(self, value: TWatched) -> None:
        self.value: TWatched = value

    @property
    def latest(self) -> TWatched:
        return self.value


# # 🥭 LamdaUpdateWatcher class
#
# The `LamdaUpdateWatcher` class provides a basic implementation of the `Watcher` protocol that
# calls a lambda to determine the latest version.
#
class LamdaUpdateWatcher(typing.Generic[TWatched]):
    def __init__(self, accessor: typing.Callable[[], TWatched]) -> None:
        self.accessor: typing.Callable[[], TWatched] = accessor

    @property
    def latest(self) -> TWatched:
        return self.accessor()
