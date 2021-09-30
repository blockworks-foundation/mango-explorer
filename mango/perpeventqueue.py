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
import typing

from datetime import datetime
from decimal import Decimal
from solana.publickey import PublicKey

from .accountinfo import AccountInfo
from .addressableaccount import AddressableAccount
from .context import Context
from .layouts import layouts
from .lotsizeconverter import LotSizeConverter
from .metadata import Metadata
from .orders import Side
from .version import Version


# # 🥭 PerpEvent class
#
# `PerpEvent` is the base class of all perp event objects.
#
class PerpEvent(metaclass=abc.ABCMeta):
    def __init__(self, event_type: int, original_index: Decimal):
        self.event_type: int = event_type
        self.original_index: Decimal = original_index

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
    def __init__(self, event_type: int, original_index: Decimal, timestamp: datetime, taker_side: Side,
                 price: Decimal, quantity: Decimal, best_initial: Decimal, maker_slot: Decimal,
                 maker_out: bool, maker: PublicKey, maker_order_id: Decimal,
                 maker_client_order_id: Decimal, taker: PublicKey, taker_order_id: Decimal,
                 taker_client_order_id: Decimal):
        super().__init__(event_type, original_index)
        self.timestamp: datetime = timestamp
        self.taker_side: Side = taker_side
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

    def __str__(self) -> str:
        return f"""« 𝙿𝚎𝚛𝚙𝙵𝚒𝚕𝚕𝙴𝚟𝚎𝚗𝚝 [{self.original_index}] [{self.timestamp}] {self.taker_side} {self.quantity:,.8f} at {self.price:,.8f}
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
    def __init__(self, event_type: int, original_index: Decimal, owner: PublicKey, side: Side,
                 quantity: Decimal, slot: Decimal):
        super().__init__(event_type, original_index)
        self.owner: PublicKey = owner
        self.side: Side = side
        self.slot: Decimal = slot
        self.quantity: Decimal = quantity

    @property
    def accounts_to_crank(self) -> typing.Sequence[PublicKey]:
        return [self.owner]

    def __str__(self) -> str:
        return f"""« 𝙿𝚎𝚛𝚙𝙾𝚞𝚝𝙴𝚟𝚎𝚗𝚝 [{self.original_index}] [{self.owner}] {self.side} {self.quantity}, slot: {self.slot} »"""


# # 🥭 PerpLiquidateEvent class
#
# `PerpLiquidateEvent` stores details of a perp 'liquidate' event.
#
class PerpLiquidateEvent(PerpEvent):
    def __init__(self, event_type: int, original_index: Decimal, timestamp: datetime, seq_num: Decimal,
                 liquidatee: PublicKey, liquidator: PublicKey, price: Decimal, quantity: Decimal,
                 liquidation_fee: Decimal):
        super().__init__(event_type, original_index)
        self.timestamp: datetime = timestamp
        self.seq_num: Decimal = seq_num
        self.liquidatee: PublicKey = liquidatee
        self.liquidator: PublicKey = liquidator
        self.price: Decimal = price
        self.quantity: Decimal = quantity
        self.liquidation_fee: Decimal = liquidation_fee

    @property
    def accounts_to_crank(self) -> typing.Sequence[PublicKey]:
        return [self.liquidatee, self.liquidator]

    def __str__(self) -> str:
        return f"""« 𝙿𝚎𝚛𝚙𝙻𝚒𝚚𝚞𝚒𝚍𝚊𝚝𝚎𝙴𝚟𝚎𝚗𝚝 Liquidator {self.liquidator} liquidated {self.liquidatee} with {self.quantity} at {self.price} »"""


# # 🥭 PerpUnknownEvent class
#
# `PerpUnknownEvent` details an unknown `PerpEvent`. This should never be encountered, but might if
# the event queue data is upgraded before this code.
#
class PerpUnknownEvent(PerpEvent):
    def __init__(self, event_type: int, original_index: Decimal, owner: PublicKey):
        super().__init__(event_type, original_index)
        self.owner: PublicKey = owner

    @property
    def accounts_to_crank(self) -> typing.Sequence[PublicKey]:
        return [self.owner]

    def __str__(self) -> str:
        return f"« 𝙿𝚎𝚛𝚙𝚄𝚗𝚔𝚗𝚘𝚠𝚗𝙴𝚟𝚎𝚗𝚝 [{self.original_index}] [{self.owner}] »"


# # 🥭 event_builder function
#
# `event_builder()` takes an event layout and returns a typed `PerpEvent`.
#
def event_builder(lot_size_converter: LotSizeConverter, event_layout, original_index: Decimal) -> typing.Optional[PerpEvent]:
    if event_layout.event_type == b'\x00':
        if event_layout.maker is None and event_layout.taker is None:
            return None
        taker_side: Side = Side.from_value(event_layout.taker_side)
        quantity: Decimal = lot_size_converter.base_size_lots_to_number(event_layout.quantity)
        price: Decimal = lot_size_converter.price_lots_to_number(event_layout.price)
        return PerpFillEvent(event_layout.event_type, original_index, event_layout.timestamp, taker_side,
                             price, quantity, event_layout.best_initial,
                             event_layout.maker_slot, event_layout.maker_out, event_layout.maker,
                             event_layout.maker_order_id, event_layout.maker_client_order_id,
                             event_layout.taker, event_layout.taker_order_id,
                             event_layout.taker_client_order_id)
    elif event_layout.event_type == b'\x01':
        return PerpOutEvent(event_layout.event_type, original_index, event_layout.owner, event_layout.side, event_layout.quantity, event_layout.slot)
    elif event_layout.event_type == b'\x02':
        return PerpLiquidateEvent(event_layout.event_type, original_index, event_layout.timestamp, event_layout.seq_num, event_layout.liquidatee, event_layout.liquidator, event_layout.price, event_layout.quantity, event_layout.liquidation_fee)
    else:
        return PerpUnknownEvent(event_layout.event_type, original_index, event_layout.owner)


# # 🥭 PerpEventQueue class
#
# `PerpEventQueue` stores details of perp events in a ringbuffer, along with indices to track which events are
# processed by 'consume events' and which are not.
#
class PerpEventQueue(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version, meta_data: Metadata,
                 head: Decimal, count: Decimal, sequence_number: Decimal,
                 unprocessed_events: typing.Sequence[PerpEvent],
                 processed_events: typing.Sequence[PerpEvent]):
        super().__init__(account_info)
        self.version: Version = version

        self.meta_data: Metadata = meta_data
        self.head: Decimal = head
        self.count: Decimal = count
        self.sequence_number: Decimal = sequence_number

        self.unprocessed_events: typing.Sequence[PerpEvent] = unprocessed_events
        self.processed_events: typing.Sequence[PerpEvent] = processed_events

    @staticmethod
    def from_layout(layout: typing.Any, account_info: AccountInfo, version: Version, lot_size_converter: LotSizeConverter) -> "PerpEventQueue":
        meta_data: Metadata = Metadata.from_layout(layout.meta_data)
        head: Decimal = layout.head
        count: Decimal = layout.count
        seq_num: Decimal = layout.seq_num
        events: typing.List[PerpEvent] = []
        for index, raw_event in enumerate(layout.events):
            built_event = event_builder(lot_size_converter, raw_event, Decimal(index))
            if built_event is not None:
                events += [built_event]

        # Events are stored in a ringbuffer, and the oldest is overwritten when a new event arrives.
        # Make it a bit simpler to use by splitting at the insertion point and swapping the two pieces
        # around so that users don't have to do modulo arithmetic on the capacity.
        ordered_events = events[int(head):] + events[0:int(head)]

        # Now chop the oldest-to-newest list of events into processed and unprocessed. The `count`
        # property holds the number of unprocessed events.
        unprocessed_events = ordered_events[0:int(count)]
        processed_events = ordered_events[int(count):]

        return PerpEventQueue(account_info, version, meta_data, head, count, seq_num, unprocessed_events, processed_events)

    @ staticmethod
    def parse(account_info: AccountInfo, lot_size_converter: LotSizeConverter) -> "PerpEventQueue":
        # Data length isn't fixed so can't check we get the right value the way we normally do.
        layout = layouts.PERP_EVENT_QUEUE.parse(account_info.data)
        return PerpEventQueue.from_layout(layout, account_info, Version.V1, lot_size_converter)

    @ staticmethod
    def load(context: Context, address: PublicKey, lot_size_converter: LotSizeConverter) -> "PerpEventQueue":
        account_info = AccountInfo.load(context, address)
        if account_info is None:
            raise Exception(f"PerpEventQueue account not found at address '{address}'")
        return PerpEventQueue.parse(account_info, lot_size_converter)

    @ property
    def capacity(self) -> int:
        return len(self.unprocessed_events) + len(self.processed_events)

    def __str__(self) -> str:
        unprocessed_events = "\n        ".join([f"{event}".replace("\n", "\n        ")
                                                for event in self.unprocessed_events if event is not None]) or "None"
        processed_events = "\n        ".join([f"{event}".replace("\n", "\n        ")
                                              for event in self.processed_events if event is not None]) or "None"
        return f"""« 𝙿𝚎𝚛𝚙𝙴𝚟𝚎𝚗𝚝𝚀𝚞𝚎𝚞𝚎 [{self.version}] {self.address}
    {self.meta_data}
    Head: {self.head}
    Count: {self.count}
    Sequence Number: {self.sequence_number}
    Capacity: {self.capacity}
    Unprocessed Events:
        {unprocessed_events}
    Processed Events:
        {processed_events}
»"""


# # 🥭 UnseenPerpEventChangesTracker class
#
# `UnseenPerpEventChangesTracker` tracks changes to a specific `PerpEventQueue`. When an updated version
# of the `PerpEventQueue` is passed to `unseen()`, any new events are returned.
#
# Seen events are tracked by keeping a 'sequence_number' index of the last event seen in the
# `PerpEventQueue` ringbuffer. When a new `PerpEventQueue` appears, the difference between its
# sequence_number and the stored sequence_number is used to calculate the number of new events
# to return.
#
class UnseenPerpEventChangesTracker:
    def __init__(self, initial: PerpEventQueue):
        self.last_sequence_number: Decimal = initial.sequence_number

    def unseen(self, event_queue: PerpEventQueue) -> typing.Sequence[PerpEvent]:
        unseen: typing.List[PerpEvent] = []
        new_sequence_number: Decimal = event_queue.sequence_number
        if self.last_sequence_number != new_sequence_number:
            number_of_changes: Decimal = new_sequence_number - self.last_sequence_number
            unseen = [*event_queue.processed_events, *event_queue.unprocessed_events][0 - int(number_of_changes):]
            self.last_sequence_number = new_sequence_number

        return unseen
