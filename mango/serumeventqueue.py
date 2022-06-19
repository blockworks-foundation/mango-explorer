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

from decimal import Decimal
from solana.publickey import PublicKey

from .accountflags import AccountFlags
from .accountinfo import AccountInfo
from .addressableaccount import AddressableAccount
from .context import Context
from .layouts import layouts
from .observables import Disposable
from .tokens import Token
from .version import Version
from .websocketsubscription import (
    WebSocketAccountSubscription,
    WebSocketSubscriptionManager,
)


# # 🥭 SerumEventFlags class
#
# `SerumEventFlags` stores flags describing a `SerumEvent`.
#
class SerumEventFlags:
    def __init__(
        self, version: Version, fill: bool, out: bool, bid: bool, maker: bool
    ) -> None:
        self.version: Version = version
        self.fill: bool = fill
        self.out: bool = out
        self.bid: bool = bid
        self.maker: bool = maker

    @staticmethod
    def from_layout(layout: typing.Any) -> "SerumEventFlags":
        return SerumEventFlags(
            Version.UNSPECIFIED,
            bool(layout.fill),
            bool(layout.out),
            bool(layout.bid),
            bool(layout.maker),
        )

    def __str__(self) -> str:
        flags: typing.List[typing.Optional[str]] = []
        flags += ["fill" if self.fill else None]
        flags += ["out" if self.out else None]
        flags += ["bid" if self.bid else None]
        flags += ["maker" if self.maker else None]
        flag_text = " | ".join(flag for flag in flags if flag is not None) or "None"
        return f"« SerumEventFlags: {flag_text} »"

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 SerumEvent class
#
# `SerumEvent` stores details of an actual event in Serum.
#
class SerumEvent:
    def __init__(
        self,
        version: Version,
        event_flags: SerumEventFlags,
        base: Token,
        quote: Token,
        open_order_slot: Decimal,
        fee_tier: Decimal,
        native_quantity_released: Decimal,
        native_quantity_paid: Decimal,
        native_fee_or_rebate: Decimal,
        order_id: Decimal,
        public_key: PublicKey,
        client_order_id: Decimal,
    ) -> None:
        self.version: Version = version
        self.event_flags: SerumEventFlags = event_flags
        self.base: Token = base
        self.quote: Token = quote
        self.open_order_slot: Decimal = open_order_slot
        self.fee_tier: Decimal = fee_tier
        self.native_quantity_released: Decimal = native_quantity_released
        self.native_quantity_paid: Decimal = native_quantity_paid
        self.native_fee_or_rebate: Decimal = native_fee_or_rebate
        self.order_id: Decimal = order_id
        self.public_key: PublicKey = public_key
        self.client_order_id: Decimal = client_order_id
        self.original_index: Decimal = Decimal(0)

    @property
    def accounts_to_crank(self) -> typing.Sequence[PublicKey]:
        return [self.public_key]

    @property
    def price(self) -> Decimal:
        if self.event_flags.bid:
            return (
                self.native_quantity_paid + self.native_fee_or_rebate
            ) / self.native_quantity_released
        else:
            return (
                self.native_quantity_released + self.native_fee_or_rebate
            ) / self.native_quantity_paid

    @property
    def quantity(self) -> Decimal:
        if self.event_flags.bid:
            return self.quote.shift_to_decimals(self.native_quantity_released)
        else:
            return self.quote.shift_to_decimals(self.native_quantity_paid)

    @staticmethod
    def from_layout(layout: typing.Any, base: Token, quote: Token) -> "SerumEvent":
        event_flags: SerumEventFlags = SerumEventFlags.from_layout(layout.event_flags)
        return SerumEvent(
            Version.UNSPECIFIED,
            event_flags,
            base,
            quote,
            layout.open_order_slot,
            layout.fee_tier,
            layout.native_quantity_released,
            layout.native_quantity_paid,
            layout.native_fee_or_rebate,
            layout.order_id,
            layout.public_key,
            layout.client_order_id,
        )

    def __str__(self) -> str:
        return f"""« SerumEvent {self.quantity:,.8f} {self.base.symbol} @ {self.price:,.8f} {self.quote.symbol}
    {self.event_flags}
    ID: {self.order_id} / {self.client_order_id}
    Index: {self.original_index}
    Owner: {self.public_key}
    Fee Tier: {self.fee_tier}
    OpenOrder Slot: {self.open_order_slot}
    Native
        Quantity Released: {self.native_quantity_released}
        Quantity Paid: {self.native_quantity_paid}
        Fee Or Rebate: {self.native_fee_or_rebate}
»"""

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 SerumEventQueue class
#
# `SerumEventQueue` stores details of recent Serum events.
#
# This implementation is a little different to other implementations, to make it easier to use.
#
# Events are split into two buckets - processed and unprocessed. Both are sorted from oldest to newest.
# Unprocessed may be empty, if there is nothing for the crank to do. Processed may be empty if the
# market is new and there hasn't been a trade on it yet.
#
class SerumEventQueue(AddressableAccount):
    def __init__(
        self,
        account_info: AccountInfo,
        version: Version,
        base: Token,
        quote: Token,
        account_flags: AccountFlags,
        head: Decimal,
        count: Decimal,
        sequence_number: Decimal,
        unprocessed_events: typing.Sequence[SerumEvent],
        processed_events: typing.Sequence[SerumEvent],
    ) -> None:
        super().__init__(account_info)
        self.version: Version = version

        self.base: Token = base
        self.quote: Token = quote

        self.account_flags: AccountFlags = account_flags
        self.head: Decimal = head
        self.count: Decimal = count
        self.sequence_number: Decimal = sequence_number
        self.unprocessed_events: typing.Sequence[SerumEvent] = unprocessed_events
        self.processed_events: typing.Sequence[SerumEvent] = processed_events

    @staticmethod
    def from_layout(
        layout: typing.Any,
        account_info: AccountInfo,
        version: Version,
        base: Token,
        quote: Token,
    ) -> "SerumEventQueue":
        account_flags: AccountFlags = AccountFlags.from_layout(layout.account_flags)
        head: Decimal = layout.head
        count: Decimal = layout.count
        seq_num: Decimal = layout.next_seq_num

        events: typing.List[SerumEvent] = []
        for index, evt in enumerate(layout.events):
            if evt is not None:
                event = SerumEvent.from_layout(evt, base, quote)
                event.original_index = Decimal(index)
                events += [event]

        # Events are stored in a ringbuffer, and the oldest is overwritten when a new event arrives.
        # Make it a bit simpler to use by splitting at the insertion point and swapping the two pieces
        # around so that users don't have to do modulo arithmetic on the capacity.
        ordered_events = events[int(head) :] + events[0 : int(head)]

        # Now chop the oldest-to-newest list of events into processed and unprocessed. The `count`
        # property holds the number of unprocessed events.
        unprocessed_events = ordered_events[0 : int(count)]
        processed_events = ordered_events[int(count) :]

        return SerumEventQueue(
            account_info,
            version,
            base,
            quote,
            account_flags,
            head,
            count,
            seq_num,
            unprocessed_events,
            processed_events,
        )

    @staticmethod
    def parse(
        account_info: AccountInfo, base: Token, quote: Token
    ) -> "SerumEventQueue":
        # Data length isn't fixed so can't check we get the right value the way we normally do.
        layout = layouts.SERUM_EVENT_QUEUE.parse(account_info.data)
        return SerumEventQueue.from_layout(
            layout, account_info, Version.V1, base, quote
        )

    @staticmethod
    def load(
        context: Context, address: PublicKey, base: Token, quote: Token
    ) -> "SerumEventQueue":
        account_info = AccountInfo.load(context, address)
        if account_info is None:
            raise Exception(f"SerumEventQueue account not found at address '{address}'")
        return SerumEventQueue.parse(account_info, base, quote)

    @property
    def accounts_to_crank(self) -> typing.Sequence[PublicKey]:
        to_crank: typing.List[PublicKey] = []
        for event_to_crank in self.unprocessed_events:
            to_crank += [event_to_crank.public_key]

        seen = []
        distinct = []
        for account in to_crank:
            account_str = account.to_base58()
            if account_str not in seen:
                distinct += [account]
                seen += [account_str]

        return distinct

    @property
    def events(self) -> typing.Sequence[SerumEvent]:
        return [*self.processed_events, *self.unprocessed_events]

    @property
    def fills(self) -> typing.Sequence[SerumEvent]:
        fills: typing.List[SerumEvent] = []
        for event in self.events:
            if event.event_flags.fill:
                fills += [event]
        return fills

    @property
    def capacity(self) -> int:
        return len(self.unprocessed_events) + len(self.processed_events)

    def subscribe(
        self,
        context: Context,
        websocketmanager: WebSocketSubscriptionManager,
        callback: typing.Callable[["SerumEventQueue"], None],
    ) -> Disposable:
        subscription = WebSocketAccountSubscription(
            context,
            self.address,
            lambda account_info: SerumEventQueue.parse(
                account_info, self.base, self.quote
            ),
        )
        websocketmanager.add(subscription)
        subscription.publisher.subscribe(on_next=callback)  # type: ignore[call-arg]

        return subscription

    def __str__(self) -> str:
        unprocessed_events = (
            "\n        ".join(
                [
                    f"{event}".replace("\n", "\n        ")
                    for event in self.unprocessed_events
                    if event is not None
                ]
            )
            or "None"
        )
        processed_events = (
            "\n        ".join(
                [
                    f"{event}".replace("\n", "\n        ")
                    for event in self.processed_events
                    if event is not None
                ]
            )
            or "None"
        )
        return f"""« SerumEventQueue [{self.version}] {self.address}
    {self.account_flags}
    Head: {self.head}
    Count: {self.count}
    Sequence Number: {self.sequence_number}
    Capacity: {self.capacity}
    Unprocessed Events:
        {unprocessed_events}
    Processed Events:
        {processed_events}
»"""


# # 🥭 UnseenSerumEventChangesTracker class
#
# `UnseenSerumEventChangesTracker` tracks changes to a specific `SerumEventQueue`. When an updated
# version of the `SerumEventQueue` is passed to `unseen()`, any new events are returned.
#
# Seen events are tracked by keeping a 'sequence_number' index of the last event seen in the
# `SerumEventQueue` ringbuffer. When a new `SerumEventQueue` appears, the difference between its
# sequence_number and the stored sequence_number is used to calculate the number of new events
# to return.
#
class UnseenSerumEventChangesTracker:
    def __init__(self, initial: SerumEventQueue) -> None:
        self.last_sequence_number: Decimal = initial.sequence_number

    def unseen(self, event_queue: SerumEventQueue) -> typing.Sequence[SerumEvent]:
        unseen: typing.List[SerumEvent] = []
        new_sequence_number: Decimal = event_queue.sequence_number
        if self.last_sequence_number != new_sequence_number:
            number_of_changes: Decimal = new_sequence_number - self.last_sequence_number
            unseen = [*event_queue.processed_events, *event_queue.unprocessed_events][
                0 - int(number_of_changes) :
            ]
            self.last_sequence_number = new_sequence_number

        return unseen
