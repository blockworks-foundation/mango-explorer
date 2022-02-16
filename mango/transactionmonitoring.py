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
import enum
import logging
import threading
import typing

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from solana.rpc.commitment import Commitment, Finalized

from .context import Context
from .client import TransactionMonitor
from .reconnectingwebsocket import ReconnectingWebsocket


class TransactionOutcome(enum.Enum):
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"
    TIMEOUT = "TIMEOUT"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self}"


@dataclass
class TransactionStatus:
    signature: str
    outcome: TransactionOutcome
    err: typing.Optional[typing.Dict[str, typing.Any]]
    sent: datetime
    duration: timedelta


class TransactionStatusCollector(metaclass=abc.ABCMeta):
    def add_transaction(self, status: TransactionStatus) -> None:
        raise NotImplementedError(
            "TransactionStatusCollector.add_transaction() is not implemented on the base type."
        )


class NullTransactionStatusCollector(TransactionStatusCollector):
    def add_transaction(self, status: TransactionStatus) -> None:
        pass


class DequeTransactionStatusCollector(TransactionStatusCollector):
    def __init__(self, maxlength: int = 100) -> None:
        self.transactions: typing.Deque[TransactionStatus] = deque(maxlen=maxlength)

    def add_transaction(self, status: TransactionStatus) -> None:
        self.transactions.append(status)


class SignatureSubscription:
    def __init__(
        self,
        signature: str,
    ) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.signature: str = signature

        self.id: int = 0
        self.subscribe_request_id: int = 0
        self.unsubscribe_request_id: int = 0
        self.started_at: datetime = datetime.now()
        self.completed_at: typing.Optional[datetime] = None
        self.timeout_timer: typing.Optional[threading.Timer] = None
        self.__final_status: typing.Optional[str] = None

    @property
    def final_status(self) -> typing.Optional[str]:
        return self.__final_status

    @final_status.setter
    def final_status(self, status: typing.Optional[str]) -> None:
        self.completed_at = datetime.now()
        self.__final_status = status

    @property
    def time_taken(self) -> timedelta:
        if self.completed_at is None:
            return timedelta(0)
        return self.completed_at - self.started_at

    @property
    def time_taken_seconds(self) -> float:
        time_taken = self.time_taken
        return time_taken.seconds + time_taken.microseconds / 1000000

    def build_subscription(self, id: int, commitment: str) -> str:
        self.subscribe_request_id = id
        return f"""{{
    "jsonrpc": "2.0",
    "id": {id},
    "method": "signatureSubscribe",
    "params": [
        "{self.signature}",
        {{
            "commitment": "{commitment}"
        }}
    ]
}}"""

    def build_unsubscription(self, id: int) -> str:
        self.unsubscribe_request_id = id
        return f"""{{
    "jsonrpc": "2.0",
    "id": {id},
    "method":"signatureUnsubscribe",
    "params": [{self.id}]
}}"""

    def build_status(
        self,
        outcome: TransactionOutcome,
        err: typing.Optional[typing.Dict[str, typing.Any]] = None,
    ) -> TransactionStatus:
        return TransactionStatus(
            self.signature,
            outcome,
            err,
            self.started_at,
            self.time_taken,
        )


class WebSocketTransactionMonitor(TransactionMonitor):
    def __init__(
        self,
        context: Context,
        commitment: Commitment = Finalized,
        timeout: float = 90.0,
        collector: TransactionStatusCollector = NullTransactionStatusCollector(),
    ) -> None:
        super().__init__()
        self.context: Context = context
        self.commitment: Commitment = commitment
        self.timeout: float = timeout
        self.collector: TransactionStatusCollector = collector

        self.__subscriptions: typing.List[SignatureSubscription] = []
        self.__ws: typing.Optional[ReconnectingWebsocket] = ReconnectingWebsocket(
            self.context.client.cluster_ws_url,
            lambda _: None,
        )
        self.__ws.ping_interval = self.context.ping_interval
        self.__ws.item.subscribe(on_next=self.__on_response)  # type: ignore[call-arg]
        self.__ws.open()
        self.__ws.connected.subscribe(on_next=self.__on_reconnect)  # type: ignore[call-arg]

    def monitor(self, signature: str) -> None:
        subscription = SignatureSubscription(signature)
        self.__subscriptions += [subscription]

        if self.__ws is None:
            raise Exception("Cannot send to websocket - it has been closed.")

        self.__ws.send(
            subscription.build_subscription(
                self.context.generate_client_id(), self.commitment
            )
        )
        timer = threading.Timer(self.timeout, lambda: self.__on_timeout(subscription))
        timer.start()
        subscription.timeout_timer = timer

    def __on_timeout(self, subscription: SignatureSubscription) -> None:
        subscription.final_status = "timeout"
        self._logger.warning(
            f"Timed out waiting for transaction with signature {subscription.signature} to reach '{self.commitment}' - gave up after {subscription.time_taken_seconds:.2f} seconds."
        )
        self.collector.add_transaction(
            subscription.build_status(TransactionOutcome.TIMEOUT)
        )

        if self.__ws is None:
            return

        self.__ws.send(
            subscription.build_unsubscription(self.context.generate_client_id())
        )

    def __on_response(self, response: typing.Any) -> None:
        if "method" not in response:
            id: int = int(response["id"])
            to_remove = [
                sub for sub in self.__subscriptions if sub.unsubscribe_request_id == id
            ]
            if len(to_remove) > 0:
                self.__subscriptions.remove(to_remove[0])
            else:
                self.__add_subscription_id(id, int(response["result"]))
        elif response["method"] == "signatureNotification":
            params = response["params"]
            id = params["subscription"]
            subscription = self.__subscription_by_subscription_id(id)
            if subscription.timeout_timer is not None:
                subscription.timeout_timer.cancel()
            self.__subscriptions.remove(subscription)
            subscription.final_status = Finalized
            slot = params["result"]["context"]["slot"]
            err = params["result"]["value"]["err"]
            if err is not None:
                self.collector.add_transaction(
                    subscription.build_status(TransactionOutcome.FAIL, err)
                )
                self._logger.warning(
                    f"Transaction {subscription.signature} failed after {subscription.time_taken_seconds:.2f} seconds with error: {err}"
                )
            else:
                self.slot_holder.require_data_from_fresh_slot(slot)
                self.collector.add_transaction(
                    subscription.build_status(TransactionOutcome.SUCCESS)
                )
                self._logger.debug(
                    f"Transaction {subscription.signature} reached status '{self.commitment}' in slot {slot} after {subscription.time_taken_seconds:.2f} seconds."
                )
        else:
            self._logger.error(f"[{self.context.name}] Unknown response: {response}")

    def __on_reconnect(self, _: datetime) -> None:
        # Our previous websocket was disconnected, so we won't hear back from it about our
        # pending signatures. Send them as new subscriptions to the fresh websocket, but
        # don't reset the timeout.
        if self.__ws is not None:
            for subscription in self.__subscriptions:
                self.__ws.send(
                    subscription.build_subscription(
                        self.context.generate_client_id(), self.commitment
                    )
                )

    def __add_subscription_id(self, subscribe_request_id: int, id: int) -> None:
        for subscription in self.__subscriptions:
            if subscription.subscribe_request_id == subscribe_request_id:
                subscription.id = id
                return
        self._logger.error(
            f"[{self.context.name}] Subscription ID {subscribe_request_id} not found"
        )

    def __subscription_by_subscription_id(self, id: int) -> SignatureSubscription:
        for subscription in self.__subscriptions:
            if subscription.id == id:
                return subscription
        raise Exception(
            f"[{self.context.name}] No subscription with subscription ID {id} could be found."
        )

    def dispose(self) -> None:
        if self.__ws is not None:
            for subscription in self.__subscriptions:
                if subscription.timeout_timer is not None:
                    subscription.timeout_timer.cancel()
                subscription.final_status = "timeout"
                self._logger.warning(
                    f"Closing WebSocketTransactionMonitor while waiting for transaction with signature {subscription.signature} to reach '{self.commitment}'."
                )
                self.collector.add_transaction(
                    subscription.build_status(TransactionOutcome.TIMEOUT)
                )

            self.__ws.close()
            self.__ws = None
