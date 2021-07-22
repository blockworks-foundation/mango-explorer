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
from .metadata import Metadata
from .orders import Side
from .version import Version


# # 🥭 PerpEventQueue class
#
# `PerpEventQueue` stores details of how to reach `PerpEventQueue```.
#


class Event(metaclass=abc.ABCMeta):
    def __init__(self, event_type: int):
        self.event_type: int = event_type

    @abc.abstractproperty
    @property
    def accounts_to_crank(self) -> typing.Sequence[PublicKey]:
        raise NotImplementedError("Event.accounts_to_crank is not implemented on the base type.")

    def __repr__(self) -> str:
        return f"{self}"


class FillEvent(Event):
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
        return f"""« 𝙵𝚒𝚕𝚕𝙴𝚟𝚎𝚗𝚝 [{self.timestamp}] {self.side} {self.quantity} at {self.price}
    Maker: {self.maker}, {self.maker_order_id} / {self.maker_client_order_id}
    Taker: {self.taker}, {self.taker_order_id} / {self.taker_client_order_id}
    Best Initial: {self.best_initial}
    Maker Slot: {self.maker_slot}
    Maker Out: {self.maker_out}
»"""


class OutEvent(Event):
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
        return f"""« 𝙾𝚞𝚝𝙴𝚟𝚎𝚗𝚝 [{self.owner}] {self.side} {self.quantity}, slot: {self.slot} »"""


class UnknownEvent(Event):
    def __init__(self, event_type: int, owner: PublicKey):
        super().__init__(event_type)
        self.owner: PublicKey = owner

    @property
    def accounts_to_crank(self) -> typing.Sequence[PublicKey]:
        return [self.owner]

    def __str__(self):
        return f"« 𝚄𝚗𝚔𝚗𝚘𝚠𝚗𝙴𝚟𝚎𝚗𝚝 [{self.owner}] »"


def event_builder(event_layout) -> Event:
    if event_layout.event_type == b'\x00':
        if event_layout.maker is None and event_layout.taker is None:
            return None
        return FillEvent(event_layout.event_type, event_layout.timestamp, event_layout.side,
                         event_layout.price, event_layout.quantity, event_layout.best_initial,
                         event_layout.maker_slot, event_layout.maker_out, event_layout.maker,
                         event_layout.maker_order_id, event_layout.maker_client_order_id,
                         event_layout.taker, event_layout.taker_order_id,
                         event_layout.taker_client_order_id)
    elif event_layout.event_type == b'\x01':
        return OutEvent(event_layout.event_type, event_layout.owner, event_layout.side, event_layout.quantity, event_layout.slot)
    else:
        return UnknownEvent(event_layout.event_type, event_layout.owner)


class PerpEventQueue(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version, meta_data: Metadata,
                 head: Decimal, count: Decimal, sequence_number: Decimal,
                 events: typing.Sequence[Event]):
        super().__init__(account_info)
        self.version: Version = version

        self.meta_data: Metadata = meta_data
        self.head: Decimal = head
        self.count: Decimal = count
        self.sequence_number: Decimal = sequence_number
        self.events: typing.Sequence[Event] = events

    @staticmethod
    def from_layout(layout: layouts.PERP_EVENT_QUEUE, account_info: AccountInfo, version: Version, data_size: int) -> "PerpEventQueue":
        meta_data: Metadata = Metadata.from_layout(layout.meta_data)
        head: Decimal = layout.head
        count: Decimal = layout.count
        seq_num: Decimal = layout.seq_num
        events: typing.Sequence[Event] = list(map(event_builder, layout.events))

        return PerpEventQueue(account_info, version, meta_data, head, count, seq_num, events)

    @ staticmethod
    def parse(account_info: AccountInfo) -> "PerpEventQueue":
        # Data length isn't fixed so can't check we get the right value the way we normally do.
        layout = layouts.PERP_EVENT_QUEUE.parse(account_info.data)
        data_size = len(account_info.data)
        return PerpEventQueue.from_layout(layout, account_info, Version.V1, data_size)

    @ staticmethod
    def load(context: Context, address: PublicKey) -> "PerpEventQueue":
        account_info = AccountInfo.load(context, address)
        if account_info is None:
            raise Exception(f"PerpEventQueue account not found at address '{address}'")
        return PerpEventQueue.parse(account_info)

    @property
    def capacity(self) -> int:
        return len(self.events)

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
