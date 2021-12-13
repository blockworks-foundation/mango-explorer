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
import typing
import websocket

from datetime import datetime
from rx.subject.behaviorsubject import BehaviorSubject
from rx.core.typing import Disposable
from solana.publickey import PublicKey
from solana.rpc.types import RPCResponse

from .accountinfo import AccountInfo
from .context import Context
from .observables import EventSource
from .reconnectingwebsocket import ReconnectingWebsocket


# # 🥭 WebSocketSubscription class
#
# The `WebSocketSubscription` maintains a mapping for an account subscription in a Solana websocket to
# an actual instantiated object.
#


TSubscriptionInstance = typing.TypeVar('TSubscriptionInstance')


class WebSocketSubscription(Disposable, typing.Generic[TSubscriptionInstance], metaclass=abc.ABCMeta):
    def __init__(self, context: Context, address: PublicKey,
                 constructor: typing.Callable[[AccountInfo], TSubscriptionInstance]) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.context: Context = context
        self.address: PublicKey = address
        self.id: int = context.generate_client_id()
        self.subscription_id: int = 0
        self.from_account_info: typing.Callable[[AccountInfo], TSubscriptionInstance] = constructor
        self.publisher: EventSource[TSubscriptionInstance] = EventSource[TSubscriptionInstance]()
        self.ws: typing.Optional[ReconnectingWebsocket] = None
        self.pong: BehaviorSubject = BehaviorSubject(datetime.now())
        self._pong_subscription: typing.Optional[Disposable] = None

    @abc.abstractmethod
    def build_request(self) -> str:
        raise NotImplementedError("WebSocketSubscription.build_request() is not implemented on the base type.")

    def open(self,) -> None:
        websocket_url: str = self.context.client.cluster_url.replace("https", "wss", 1)

        def on_open(sock: websocket.WebSocketApp) -> None:
            sock.send(self.build_request())
        ws: ReconnectingWebsocket = ReconnectingWebsocket(websocket_url, on_open)
        ws.item.subscribe(on_next=self._on_item)  # type: ignore[call-arg]
        ws.ping_interval = self.context.ping_interval
        self.ws = ws
        ws.open()
        self._pong_subscription = ws.pong.subscribe(self.pong)

    def close(self) -> None:
        if self.ws is not None:
            if self._pong_subscription is not None:
                self._pong_subscription.dispose()
                self._pong_subscription = None
            self.ws.close()
            self.ws = None

    def _on_item(self, response: typing.Dict[str, typing.Any]) -> None:
        if "method" not in response:
            id: int = int(response["id"])
            if id == self.id:
                subscription_id: int = int(response["result"])
                self._logger.info(f"Subscription created with id {subscription_id}.")
        elif (response["method"] == "accountNotification") or (response["method"] == "programNotification") or (response["method"] == "logsNotification"):
            subscription_id = response["params"]["subscription"]
            built = self.build_subscribed_instance(response["params"])
            self.publisher.publish(built)
        else:
            self._logger.error(f"[{self.context.name}] Unknown response: {response}")

    def build_subscribed_instance(self, response: RPCResponse) -> TSubscriptionInstance:
        account_info: AccountInfo = AccountInfo.from_response(response, self.address)
        built: TSubscriptionInstance = self.from_account_info(account_info)
        return built

    def dispose(self) -> None:
        self.publisher.on_completed()
        self.publisher.dispose()
        if self.ws is not None:
            if self._pong_subscription is not None:
                self._pong_subscription.dispose()
                self._pong_subscription = None
            self.ws.close()
            self.ws = None


class WebSocketProgramSubscription(WebSocketSubscription[TSubscriptionInstance]):
    def __init__(self, context: Context, address: PublicKey,
                 constructor: typing.Callable[[AccountInfo], TSubscriptionInstance]) -> None:
        super().__init__(context, address, constructor)

    def build_request(self) -> str:
        return """
{
    "jsonrpc": "2.0",
    "id": \"""" + str(self.id) + """\",
    "method": "programSubscribe",
    "params": [\"""" + str(self.address) + """\",
        {
            "encoding": "base64",
            "commitment": \"""" + str(self.context.client.commitment) + """\"
        }
  ]
}
"""


class WebSocketAccountSubscription(WebSocketSubscription[TSubscriptionInstance]):
    def __init__(self, context: Context, address: PublicKey,
                 constructor: typing.Callable[[AccountInfo], TSubscriptionInstance]) -> None:
        super().__init__(context, address, constructor)

    def build_request(self) -> str:
        return """
{
    "jsonrpc": "2.0",
    "id": \"""" + str(self.id) + """\",
    "method": "accountSubscribe",
    "params": [\"""" + str(self.address) + """\",
        {
            "encoding": "base64",
           "commitment": \"""" + str(self.context.client.commitment) + """\"
        }
    ]
}
"""


class LogEvent:
    def __init__(self, signatures: typing.Sequence[str], logs: typing.Sequence[str]) -> None:
        self.signatures: typing.Sequence[str] = signatures
        self.logs: typing.Sequence[str] = logs

    @staticmethod
    def from_response(response: RPCResponse) -> "LogEvent":
        signature_text: str = response["result"]["value"]["signature"]
        signatures = signature_text.split(",")
        logs = response["result"]["value"]["logs"]
        return LogEvent(signatures, logs)

    def __str__(self) -> str:
        logs = "\n    ".join(self.logs)
        return f"""« LogEvent {self.signatures}
    {logs}
»"""

    def __repr__(self) -> str:
        return f"{self}"


class WebSocketLogSubscription(WebSocketSubscription[LogEvent]):
    def __init__(self, context: Context, address: PublicKey) -> None:
        super().__init__(context, address, lambda _: LogEvent([""], []))

    def build_request(self) -> str:
        return """
{
    "jsonrpc": "2.0",
    "id": \"""" + str(self.id) + """\",
    "method": "logsSubscribe",
    "params": [
        {
            "mentions": [ \"""" + str(self.address) + """\" ]
        },
        {
            "commitment": \"""" + str(self.context.client.commitment) + """\"
        }
    ]
}
"""

    def build(self, response: RPCResponse) -> LogEvent:
        return LogEvent.from_response(response)


# # 🥭 WebSocketSubscriptionManager class
#
# The `WebSocketSubscriptionManager` is a base class for different websocket management approaches.
#
class WebSocketSubscriptionManager(Disposable, metaclass=abc.ABCMeta):
    def __init__(self, context: Context, ping_interval: int = 10) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.context: Context = context
        self.ping_interval: int = ping_interval
        self.subscriptions: typing.List[WebSocketSubscription[typing.Any]] = []

    def add(self, subscription: WebSocketSubscription[typing.Any]) -> None:
        self.subscriptions += [subscription]

    def open(self) -> None:
        raise NotImplementedError("WebSocketSubscription.build_request() is not implemented on the base type.")

    def close(self) -> None:
        raise NotImplementedError("WebSocketSubscription.build_request() is not implemented on the base type.")

    def on_disconnected(self, ws: websocket.WebSocketApp) -> None:
        for subscription in self.subscriptions:
            subscription.dispose()
        self.subscriptions = []

    def dispose(self) -> None:
        for subscription in self.subscriptions:
            subscription.dispose()


# # 🥭 IndividualWebSocketSubscriptionManager class
#
# The `IndividualWebSocketSubscriptionManager` runs `WebSocketSubscription`s each in their own websocket.
#
class IndividualWebSocketSubscriptionManager(WebSocketSubscriptionManager):
    def __init__(self, context: Context, ping_interval: int = 10) -> None:
        super().__init__(context, ping_interval)

    def open(self) -> None:
        for subscription in self.subscriptions:
            subscription.open()

    def close(self) -> None:
        for subscription in self.subscriptions:
            subscription.close()


# # 🥭 SharedWebSocketSubscriptionManager class
#
# The `SharedWebSocketSubscriptionManager` runs a single websocket and sends updates to the correct
# `WebSocketSubscription`.
#
class SharedWebSocketSubscriptionManager(WebSocketSubscriptionManager):
    def __init__(self, context: Context, ping_interval: int = 10) -> None:
        super().__init__(context, ping_interval)
        self.ws: typing.Optional[ReconnectingWebsocket] = None
        self.pong: BehaviorSubject = BehaviorSubject(datetime.now())
        self._pong_subscription: typing.Optional[Disposable] = None

    def open(self) -> None:
        websocket_url = self.context.client.cluster_url.replace("https", "wss", 1)
        ws: ReconnectingWebsocket = ReconnectingWebsocket(websocket_url, self.open_handler)
        ws.item.subscribe(on_next=self.on_item)  # type: ignore[call-arg]
        ws.ping_interval = self.ping_interval
        self.ws = ws
        ws.open()
        self._pong_subscription = ws.pong.subscribe(self.pong)

    def close(self) -> None:
        if self.ws is not None:
            if self._pong_subscription is not None:
                self._pong_subscription.dispose()
                self._pong_subscription = None
            self.ws.close()
            self.ws = None

    def add_subscription_id(self, id: int, subscription_id: int) -> None:
        for subscription in self.subscriptions:
            if subscription.id == id:
                self._logger.info(
                    f"Setting ID {subscription_id} on subscription {subscription.id} for {subscription.address}.")
                subscription.subscription_id = subscription_id
                return
        self._logger.error(f"[{self.context.name}] Subscription ID {id} not found")

    def subscription_by_subscription_id(self, subscription_id: int) -> WebSocketSubscription[typing.Any]:
        for subscription in self.subscriptions:
            if subscription.subscription_id == subscription_id:
                return subscription
        raise Exception(f"[{self.context.name}] No subscription with subscription ID {subscription_id} could be found.")

    def on_item(self, response: typing.Dict[str, typing.Any]) -> None:
        if "method" not in response:
            id: int = int(response["id"])
            subscription_id: int = int(response["result"])
            self.add_subscription_id(id, subscription_id)
        elif (response["method"] == "accountNotification") or (response["method"] == "programNotification") or (response["method"] == "logsNotification"):
            subscription_id = response["params"]["subscription"]
            subscription = self.subscription_by_subscription_id(subscription_id)
            built = subscription.build_subscribed_instance(response["params"])
            subscription.publisher.publish(built)
        else:
            self._logger.error(f"[{self.context.name}] Unknown response: {response}")

    def open_handler(self, ws: websocket.WebSocketApp) -> None:
        for subscription in self.subscriptions:
            ws.send(subscription.build_request())

    def dispose(self) -> None:
        super().dispose()
        if self.ws is not None:
            if self._pong_subscription is not None:
                self._pong_subscription.dispose()
                self._pong_subscription = None
            self.ws.close()
            self.ws = None
