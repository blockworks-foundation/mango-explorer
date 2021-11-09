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

import rx
import typing

from pathlib import Path


# # 🥭 HealthCheck class
#
# `HealthCheck` adds an observable to the health checks. Current version touches a file when a new item
# is observed from that observable, so that external systems can watch those files and gain insight into
# the health of the system.
#
class HealthCheck(rx.core.typing.Disposable):
    def __init__(self, healthcheck_files_location: str = "/var/tmp") -> None:
        self.healthcheck_files_location: str = healthcheck_files_location
        self._to_dispose: typing.List[rx.core.typing.Disposable] = []

    def add(self, name: str, observable: rx.core.typing.Observable[typing.Any]) -> None:
        healthcheck_file_touch_disposer = observable.subscribe(
            on_next=lambda _: self.ping(name))  # type: ignore[call-arg]
        self._to_dispose += [healthcheck_file_touch_disposer]

    def ping(self, name: str) -> None:
        Path(f"{self.healthcheck_files_location}/mango_healthcheck_{name}").touch(mode=0o666, exist_ok=True)

    def dispose(self) -> None:
        for disposable in self._to_dispose:
            disposable.dispose()
