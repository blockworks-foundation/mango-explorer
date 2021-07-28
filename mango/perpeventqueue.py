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
import pyserum.enums
import typing

from datetime import datetime
from decimal import Decimal
from solana.publickey import PublicKey

from .accountinfo import AccountInfo
from .addressableaccount import AddressableAccount
from .context import Context
from .layouts import layouts
from .metadata import Metadata
from .orders import Side
from .version import Version


# # 🥭 PerpEvent class
#
# `PerpEvent` is the base class of all perp event objects.
#
class PerpEvent(metaclass=abc.ABCMeta):
    def __init__(self, event_type: int):
        self.event_type: int = event_type

    @abc.abstractproperty
    @property
    def accounts_to_crank(self) -> typing.Sequence[PublicKey]:
        raise NotImplementedError("PerpEvent.accounts_to_crank is not implemented on the base type.")

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 PerpFillEvent class
#
# `PerpOutEvent` stores details of a perp 'fill' event.
#
class PerpFillEvent(PerpEvent):
    def __init__(self, event_type: int, timestamp: datetime, side: Side, price: Decimal, quantity: Decimal,
                 best_initial: Decimal, maker_slot: Decimal, maker_out: bool,
                 maker: PublicKey, maker_order_id: Decimal, maker_client_order_id: Decimal,
                 taker: PublicKey, taker_order_id: Decimal, taker_client_order_id: Decimal):
        super().__init__(event_type)
        self.timestamp: datetime = timestamp
        self.side: Side = side
        self.price: Decimal = price
        self.quantity: Decimal = quantity

        self.best_initial: Decimal = best_initial
        self.maker_slot: Decimal = maker_slot
        self.maker_out: bool = maker_out

        self.maker: PublicKey = maker
        self.maker_order_id: Decimal = maker_order_id
        self.maker_client_order_id: Decimal = maker_client_order_id

        self.taker: PublicKey = taker
        self.taker_order_id: Decimal = taker_order_id
        self.taker_client_order_id: Decimal = taker_client_order_id

    @property
    def accounts_to_crank(self) -> typing.Sequence[PublicKey]:
        return [self.maker, self.taker]

    def __str__(self):
        return f"""« 𝙿𝚎𝚛𝚙𝙵𝚒𝚕𝚕𝙴𝚟𝚎𝚗𝚝 [{self.timestamp}] {self.side} {self.quantity:,.8f} at {self.price:,.8f}
    Maker: {self.maker}, {self.maker_order_id} / {self.maker_client_order_id}
    Taker: {self.taker}, {self.taker_order_id} / {self.taker_client_order_id}
    Best Initial: {self.best_initial}
    Maker Slot: {self.maker_slot}
    Maker Out: {self.maker_out}
»"""


# # 🥭 PerpOutEvent class
#
# `PerpOutEvent` stores details of a perp 'out' event.
#
class PerpOutEvent(PerpEvent):
    def __init__(self, event_type: int, owner: PublicKey, side: Side, quantity: Decimal, slot: Decimal):
        super().__init__(event_type)
        self.owner: PublicKey = owner
        self.side: Side = side
        self.slot: Decimal = slot
        self.quantity: Decimal = quantity

    @property
    def accounts_to_crank(self) -> typing.Sequence[PublicKey]:
        return [self.owner]

    def __str__(self):
        return f"""« 𝙿𝚎𝚛𝚙𝙾𝚞𝚝𝙴𝚟𝚎𝚗𝚝 [{self.owner}] {self.side} {self.quantity}, slot: {self.slot} »"""


# # 🥭 PerpUnknownEvent class
#
# `PerpUnknownEvent` details an unknown `PerpEvent`. This should never be encountered, but might if
# the event queue data is upgraded before this code.
#
class PerpUnknownEvent(PerpEvent):
    def __init__(self, event_type: int, owner: PublicKey):
        super().__init__(event_type)
        self.owner: PublicKey = owner

    @property
    def accounts_to_crank(self) -> typing.Sequence[PublicKey]:
        return [self.owner]

    def __str__(self):
        return f"« 𝙿𝚎𝚛𝚙𝚄𝚗𝚔𝚗𝚘𝚠𝚗𝙴𝚟𝚎𝚗𝚝 [{self.owner}] »"


# # 🥭 event_builder function
#
# `event_builder()` takes an event layout and returns a typed `PerpEvent`.
#
def event_builder(event_layout) -> typing.Optional[PerpEvent]:
    if event_layout.event_type == b'\x00':
        if event_layout.maker is None and event_layout.taker is None:
            return None
        side: Side = Side.BUY if event_layout.side == pyserum.enums.Side.BUY else Side.SELL
        return PerpFillEvent(event_layout.event_type, event_layout.timestamp, side,
                             event_layout.price, event_layout.quantity, event_layout.best_initial,
                             event_layout.maker_slot, event_layout.maker_out, event_layout.maker,
                             event_layout.maker_order_id, event_layout.maker_client_order_id,
                             event_layout.taker, event_layout.taker_order_id,
                             event_layout.taker_client_order_id)
    elif event_layout.event_type == b'\x01':
        return PerpOutEvent(event_layout.event_type, event_layout.owner, event_layout.side, event_layout.quantity, event_layout.slot)
    else:
        return PerpUnknownEvent(event_layout.event_type, event_layout.owner)


# # 🥭 PerpEventQueue class
#
# `PerpEventQueue` stores details of perp events in a ringbuffer, along with indices to track which events are
# processed by 'consume events' and which are not.
#
class PerpEventQueue(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version, meta_data: Metadata,
                 head: Decimal, count: Decimal, sequence_number: Decimal,
                 events: typing.Sequence[typing.Optional[PerpEvent]]):
        super().__init__(account_info)
        self.version: Version = version

        self.meta_data: Metadata = meta_data
        self.head: Decimal = head
        self.count: Decimal = count
        self.sequence_number: Decimal = sequence_number
        self.events: typing.Sequence[typing.Optional[PerpEvent]] = events

    @staticmethod
    def from_layout(layout: layouts.PERP_EVENT_QUEUE, account_info: AccountInfo, version: Version) -> "PerpEventQueue":
        meta_data: Metadata = Metadata.from_layout(layout.meta_data)
        head: Decimal = layout.head
        count: Decimal = layout.count
        seq_num: Decimal = layout.seq_num
        events: typing.Sequence[typing.Optional[PerpEvent]] = list(map(event_builder, layout.events))

        return PerpEventQueue(account_info, version, meta_data, head, count, seq_num, events)

    @ staticmethod
    def parse(account_info: AccountInfo) -> "PerpEventQueue":
        # Data length isn't fixed so can't check we get the right value the way we normally do.
        layout = layouts.PERP_EVENT_QUEUE.parse(account_info.data)
        return PerpEventQueue.from_layout(layout, account_info, Version.V1)

    @ staticmethod
    def load(context: Context, address: PublicKey) -> "PerpEventQueue":
        account_info = AccountInfo.load(context, address)
        if account_info is None:
            raise Exception(f"PerpEventQueue account not found at address '{address}'")
        return PerpEventQueue.parse(account_info)

    @property
    def capacity(self) -> int:
        return len(self.events)

    def unprocessed_events(self) -> typing.Sequence[PerpEvent]:
        unprocessed: typing.List[PerpEvent] = []
        for index in range(int(self.count)):
            modulo_index = (self.head + index) % self.capacity
            event: typing.Optional[PerpEvent] = self.events[int(modulo_index)]
            if event is None:
                raise Exception(f"Event at index {index} should not be None.")
            unprocessed += [event]
        return unprocessed

    def __str__(self):
        events = "\n        ".join([f"{event}".replace("\n", "\n        ")
                                    for event in self.events if event is not None]) or "None"
        return f"""« 𝙿𝚎𝚛𝚙𝙴𝚟𝚎𝚗𝚝𝚀𝚞𝚎𝚞𝚎 [{self.version}] {self.address}
    {self.meta_data}
    Head: {self.head}
    Count: {self.count}
    Sequence Number: {self.sequence_number}
    Capacity: {self.capacity}
    Events:
        {events}
»"""


# # 🥭 UnseenPerpEventChangesTracker class
#
# `UnseenPerpEventChangesTracker` tracks changes to a specific `PerpEventQueue`. When an updated version of the
# `PerpEventQueue` is passed to `unseen()`, any new events are returned.
#
# Seen events are tracked by keeping a 'head' index of the last event seen in the `PerpEventQueue` ringbuffer.
# When a new `PerpEventQueue` appears, its head+count is used to calculate the new seen head, and events from
# the old seen head to the new seen head are returned.
#
class UnseenPerpEventChangesTracker:
    def __init__(self, initial: PerpEventQueue):
        self.last_head: Decimal = initial.head

    def unseen(self, event_queue: PerpEventQueue) -> typing.Sequence[typing.Optional[PerpEvent]]:
        unseen: typing.List[PerpEvent] = []
        new_head: Decimal = event_queue.head
        if self.last_head != new_head:
            to_process: int = int((event_queue.capacity + new_head - self.last_head) % event_queue.capacity)
            for index in range(to_process):
                modulo_index = (self.last_head + index) % event_queue.capacity
                event: typing.Optional[PerpEvent] = event_queue.events[int(modulo_index)]
                if event is None:
                    raise Exception(f"Event at index {index} should not be None.")
                unseen += [event]
            self.last_head = new_head % event_queue.capacity

        return unseen
