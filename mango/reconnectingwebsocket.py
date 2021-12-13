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


import json
import logging
import rx
import rx.subject
import typing
import websocket

from datetime import datetime
from threading import Thread


# # 🥭 ReconnectingWebsocket class
#
# The `ReconnectingWebsocket` class wraps a websocket with an automatic-reconnection
# mechanism. If an error disconnects the websocket, it will automatically reconnect. It
# will continue to automatically reconnect, until it is explicitly closed.
#
class ReconnectingWebsocket:
    def __init__(self,
                 url: str,
                 on_open_call: typing.Callable[[websocket.WebSocketApp], None]) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.url = url
        self.on_open_call = on_open_call
        self.reconnect_required: bool = True
        self.ping_interval: int = 0
        self.connecting: rx.subject.behaviorsubject.BehaviorSubject = rx.subject.behaviorsubject.BehaviorSubject(
            datetime.now())
        self.disconnected: rx.subject.behaviorsubject.BehaviorSubject = rx.subject.behaviorsubject.BehaviorSubject(
            datetime.now())
        self.ping: rx.subject.behaviorsubject.BehaviorSubject = rx.subject.behaviorsubject.BehaviorSubject(
            datetime.now())
        self.pong: rx.subject.behaviorsubject.BehaviorSubject = rx.subject.behaviorsubject.BehaviorSubject(
            datetime.now())
        self.item: rx.subject.subject.Subject = rx.subject.subject.Subject()

    def close(self) -> None:
        self._logger.info(f"Closing WebSocket for {self.url}")
        self.reconnect_required = False
        self._ws.close()

    def force_reconnect(self) -> None:
        self._logger.info(f"Forcing a reconnect on WebSocket for {self.url}")
        self._ws.close()

    def _on_open(self, ws: websocket.WebSocketApp) -> None:
        self._logger.info(f"Opening WebSocket for {self.url}")
        if self.on_open_call:
            self.on_open_call(ws)

    def _on_message(self, _: typing.Any, message: str) -> None:
        data = json.loads(message)
        self.item.on_next(data)

    def _on_error(self, *args: typing.Any) -> None:
        self._logger.warning(f"WebSocket for {self.url} has error {args}")

    def _on_ping(self, *_: typing.Any) -> None:
        self.ping.on_next(datetime.now())

    def _on_pong(self, *_: typing.Any) -> None:
        self.pong.on_next(datetime.now())

    def open(self) -> None:
        thread = Thread(target=self._run)
        thread.start()

    def send(self, message: str) -> None:
        self._ws.send(message)

    def _run(self) -> None:
        while self.reconnect_required:
            self._logger.info(f"WebSocket connecting to: {self.url}")
            self.connecting.on_next(datetime.now())
            self._ws = websocket.WebSocketApp(
                self.url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_ping=self._on_ping,
                on_pong=self._on_pong
            )
            self._ws.run_forever(ping_interval=self.ping_interval)
            self.disconnected.on_next(datetime.now())
