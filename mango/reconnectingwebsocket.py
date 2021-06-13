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
import typing
import websocket  # type: ignore

from threading import Thread


# # 🥭 ReconnectingWebsocket class
#
# The `ReconnectingWebsocket` class wraps a websocket with an automatic-reconnection
# mechanism. If an error disconnects the websocket, it will automatically reconnect. It
# will continue to automatically reconnect, until it is explicitly closed.
#


class ReconnectingWebsocket:
    def __init__(self, url: str, on_open_message: str, on_item: typing.Callable[[typing.Any], typing.Any]):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.url = url
        self.on_open_message = on_open_message
        self._on_item = on_item
        self.reconnect_required: bool = True

    def close(self):
        self.logger.info(f"Closing WebSocket for {self.url}")
        self.reconnect_required = False
        self._ws.close()

    def _on_open(self, ws):
        self.logger.info(f"Opening WebSocket for {self.url}")
        if self.on_open_message:
            ws.send(self.on_open_message)

    def _on_message(self, _, message):
        data = json.loads(message)
        self._on_item(data)

    def _on_error(self, *args):
        self.logger.warning(f"WebSocket for {self.url} has error {args}")

    def open(self):
        thread = Thread(target=self._run)
        thread.start()

    def _run(self):
        while self.reconnect_required:
            self.logger.info(f"WebSocket connecting to: {self.url}")
            self._ws = websocket.WebSocketApp(
                self.url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error
            )
            self._ws.run_forever()
