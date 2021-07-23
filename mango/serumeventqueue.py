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
from .version import Version


# # 🥭 SerumEventQueue class
#
# `SerumEventQueue` stores details of how to reach `SerumEventQueue```.
#


class SerumEventFlags:
    def __init__(self, version: Version, fill: bool, out: bool, bid: bool, maker: bool):
        self.version: Version = version
        self.fill: bool = fill
        self.out: bool = out
        self.bid: bool = bid
        self.maker: bool = maker

    @staticmethod
    def from_layout(layout: layouts.SERUM_EVENT_FLAGS) -> "SerumEventFlags":
        return SerumEventFlags(Version.UNSPECIFIED, bool(layout.fill), bool(layout.out), bool(layout.bid), bool(layout.maker))

    def __str__(self) -> str:
        flags: typing.List[typing.Optional[str]] = []
        flags += ["fill" if self.fill else None]
        flags += ["out" if self.out else None]
        flags += ["bid" if self.bid else None]
        flags += ["maker" if self.maker else None]
        flag_text = " | ".join(flag for flag in flags if flag is not None) or "None"
        return f"« 𝚂𝚎𝚛𝚞𝚖𝙴𝚟𝚎𝚗𝚝𝙵𝚕𝚊𝚐𝚜: {flag_text} »"

    def __repr__(self) -> str:
        return f"{self}"


class SerumEvent:
    def __init__(self, version: Version, event_flags: SerumEventFlags, open_order_slot: Decimal, fee_tier: Decimal,
                 native_quantity_released: Decimal, native_quantity_paid: Decimal, native_fee_or_rebate: Decimal,
                 order_id: Decimal, public_key: PublicKey, client_order_id: Decimal):
        self.version: Version = version
        self.event_flags: SerumEventFlags = event_flags
        self.open_order_slot: Decimal = open_order_slot
        self.fee_tier: Decimal = fee_tier
        self.native_quantity_released: Decimal = native_quantity_released
        self.native_quantity_paid: Decimal = native_quantity_paid
        self.native_fee_or_rebate: Decimal = native_fee_or_rebate
        self.order_id: Decimal = order_id
        self.public_key: PublicKey = public_key
        self.client_order_id: Decimal = client_order_id

    @staticmethod
    def from_layout(layout: layouts.SERUM_EVENT) -> "SerumEvent":
        event_flags: SerumEventFlags = SerumEventFlags.from_layout(layout.event_flags)
        return SerumEvent(Version.UNSPECIFIED, event_flags, layout.open_order_slot, layout.fee_tier,
                          layout.native_quantity_released, layout.native_quantity_paid, layout.native_fee_or_rebate,
                          layout.order_id, layout.public_key, layout.client_order_id)

    def __str__(self):
        return f"""« 𝚂𝚎𝚛𝚞𝚖𝙴𝚟𝚎𝚗𝚝 {self.event_flags}
    Order ID: {self.order_id}
    Client Order ID: {self.client_order_id}
    Public Key: {self.public_key}
    OpenOrder Slot: {self.open_order_slot}
    Native Quantity Released: {self.native_quantity_released}
    Native Quantity Paid: {self.native_quantity_paid}
    Native Fee Or Rebate: {self.native_fee_or_rebate}
    Fee Tier: {self.fee_tier}
»"""


class SerumEventQueue(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version, account_flags: AccountFlags,
                 head: Decimal, count: Decimal, sequence_number: Decimal,
                 events: typing.Sequence[typing.Optional[SerumEvent]]):
        super().__init__(account_info)
        self.version: Version = version

        self.account_flags: AccountFlags = account_flags
        self.head: Decimal = head
        self.count: Decimal = count
        self.sequence_number: Decimal = sequence_number
        self.events: typing.Sequence[typing.Optional[SerumEvent]] = events

    @staticmethod
    def from_layout(layout: layouts.SERUM_EVENT_QUEUE, account_info: AccountInfo, version: Version) -> "SerumEventQueue":
        account_flags: AccountFlags = AccountFlags.from_layout(layout.account_flags)
        head: Decimal = layout.head
        count: Decimal = layout.count
        seq_num: Decimal = layout.next_seq_num
        events: typing.Sequence[typing.Optional[SerumEvent]] = list(map(SerumEvent.from_layout, layout.events))

        return SerumEventQueue(account_info, version, account_flags, head, count, seq_num, events)

    @ staticmethod
    def parse(account_info: AccountInfo) -> "SerumEventQueue":
        # Data length isn't fixed so can't check we get the right value the way we normally do.
        layout = layouts.SERUM_EVENT_QUEUE.parse(account_info.data)
        return SerumEventQueue.from_layout(layout, account_info, Version.V1)

    @ staticmethod
    def load(context: Context, address: PublicKey) -> "SerumEventQueue":
        account_info = AccountInfo.load(context, address)
        if account_info is None:
            raise Exception(f"SerumEventQueue account not found at address '{address}'")
        return SerumEventQueue.parse(account_info)

    @property
    def capacity(self) -> int:
        return len(self.events)

    def unprocessed_events(self) -> typing.Sequence[SerumEvent]:
        unprocessed: typing.List[SerumEvent] = []
        for index in range(int(self.count)):
            modulo_index = (self.head + index) % self.capacity
            event: typing.Optional[SerumEvent] = self.events[int(modulo_index)]
            if event is None:
                raise Exception(f"Event at index {index} should not be None.")
            unprocessed += [event]
        return unprocessed

    def __str__(self):
        events = "\n        ".join([f"{event}".replace("\n", "\n        ")
                                    for event in self.events if event is not None]) or "None"
        return f"""« 𝚂𝚎𝚛𝚞𝚖𝙴𝚟𝚎𝚗𝚝𝚀𝚞𝚎𝚞𝚎 [{self.version}] {self.address}
    {self.account_flags}
    Head: {self.head}
    Count: {self.count}
    Sequence Number: {self.sequence_number}
    Capacity: {self.capacity}
    Events:
        {events}
»"""
