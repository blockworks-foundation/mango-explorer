import typing

from solana.publickey import PublicKey

from .context import mango
from .fakes import fake_account_info, fake_seeded_public_key

from decimal import Decimal


def test_constructor() -> None:
    address = fake_seeded_public_key("perp event queue address")
    account_info: mango.AccountInfo = fake_account_info(address)
    meta_data: mango.Metadata = mango.Metadata(mango.layouts.DATA_TYPE.EventQueue, mango.Version.V1, True)
    head: Decimal = Decimal(0)
    count: Decimal = Decimal(0)
    sequence_number: Decimal = Decimal(0)
    unprocessed_events: typing.Sequence[mango.PerpEvent] = []
    processed_events: typing.Sequence[mango.PerpEvent] = []

    actual = mango.PerpEventQueue(account_info, mango.Version.V1, meta_data, head, count,
                                  sequence_number, unprocessed_events, processed_events)
    assert actual is not None
    assert actual.logger is not None
    assert actual.account_info == account_info
    assert actual.meta_data == meta_data
    assert actual.address == address
    assert actual.head == head
    assert actual.count == count
    assert actual.sequence_number == sequence_number
    assert actual.unprocessed_events == unprocessed_events
    assert actual.processed_events == processed_events


def _fake_pev(head: Decimal, count: Decimal, sequence_number: Decimal, unprocessed: typing.Sequence[mango.PerpEvent], processed: typing.Sequence[mango.PerpEvent]) -> mango.PerpEventQueue:
    address = fake_seeded_public_key("perp event queue address")
    account_info: mango.AccountInfo = fake_account_info(address)
    meta_data: mango.Metadata = mango.Metadata(mango.layouts.DATA_TYPE.EventQueue, mango.Version.V1, True)
    return mango.PerpEventQueue(account_info, mango.Version.V1, meta_data, head, count, sequence_number, unprocessed, processed)


class TstPE(mango.PerpEvent):
    def __init__(self, event_type: int = 25, original_index: Decimal = Decimal(0)):
        super().__init__(event_type, original_index)

    @property
    def accounts_to_crank(self) -> typing.Sequence[PublicKey]:
        return []

    def __str__(self) -> str:
        return f"« TstPE [{self.event_type}] »"


def test_unseen_with_no_changes() -> None:
    initial = _fake_pev(Decimal(5), Decimal(2), Decimal(7), [], [TstPE(), TstPE(), TstPE(), TstPE(), TstPE()])
    actual: mango.UnseenPerpEventChangesTracker = mango.UnseenPerpEventChangesTracker(initial)
    assert actual.last_sequence_number == Decimal(7)

    updated = _fake_pev(Decimal(5), Decimal(2), Decimal(7), [], [TstPE(), TstPE(), TstPE(), TstPE(), TstPE()])
    unseen = actual.unseen(updated)
    assert len(unseen) == 0
    assert actual.last_sequence_number == Decimal(7)


def test_unseen_with_one_unprocessed_change() -> None:
    initial = _fake_pev(Decimal(1), Decimal(0), Decimal(1), [TstPE()], [TstPE(), TstPE(), TstPE(), TstPE()])
    actual: mango.UnseenPerpEventChangesTracker = mango.UnseenPerpEventChangesTracker(initial)
    assert actual.last_sequence_number == Decimal(1)

    marker = TstPE(50)
    updated = _fake_pev(Decimal(2), Decimal(1), Decimal(2), [marker], [TstPE(), TstPE(), TstPE(), TstPE()])
    unseen = actual.unseen(updated)
    assert actual.last_sequence_number == Decimal(2)
    assert len(unseen) == 1
    assert unseen[0] == marker


def test_unseen_with_two_unprocessed_changes() -> None:
    initial = _fake_pev(Decimal(1), Decimal(0), Decimal(1), [], [TstPE(), TstPE(), TstPE()])
    actual: mango.UnseenPerpEventChangesTracker = mango.UnseenPerpEventChangesTracker(initial)
    assert actual.last_sequence_number == Decimal(1)

    marker1 = TstPE(50)
    marker2 = TstPE(51)
    updated = _fake_pev(Decimal(3), Decimal(2), Decimal(3), [marker1, marker2], [TstPE(), TstPE(), TstPE()])
    unseen = actual.unseen(updated)
    assert actual.last_sequence_number == Decimal(3)
    assert len(unseen) == 2
    assert unseen[0] == marker1
    assert unseen[1] == marker2


def test_unseen_with_two_processed_changes() -> None:
    # This should be identical to the previous test - it shouldn't matter to 'seen' tracking whether an event
    # is processed or not.
    initial = _fake_pev(Decimal(1), Decimal(0), Decimal(1), [], [TstPE(), TstPE(), TstPE()])
    actual: mango.UnseenPerpEventChangesTracker = mango.UnseenPerpEventChangesTracker(initial)
    assert actual.last_sequence_number == Decimal(1)

    marker1 = TstPE(50)
    marker2 = TstPE(51)
    updated = _fake_pev(Decimal(3), Decimal(0), Decimal(3), [marker1, marker2], [TstPE(), TstPE(), TstPE()])
    unseen = actual.unseen(updated)
    assert actual.last_sequence_number == Decimal(3)
    assert len(unseen) == 2
    assert unseen[0] == marker1
    assert unseen[1] == marker2


def test_unseen_with_two_unprocessed_changes_wrapping_around() -> None:
    # This is tricky because the change overlaps the end of the array-as-ringbuffer. A change is added
    # to the next slot (which is the last slot in the array) and then another is added to the next slot
    # (which is the first slot in the array). Seen tracking shouldn't care - it should just return the
    # unseen events in the proper order.
    initial = _fake_pev(Decimal(4), Decimal(0), Decimal(7), [], [TstPE(), TstPE(), TstPE()])
    actual: mango.UnseenPerpEventChangesTracker = mango.UnseenPerpEventChangesTracker(initial)
    assert actual.last_sequence_number == Decimal(7)

    marker1 = TstPE(50)
    marker2 = TstPE(51)
    updated = _fake_pev(Decimal(1), Decimal(2), Decimal(9), [marker1, marker2], [TstPE(), TstPE(), TstPE()])
    unseen = actual.unseen(updated)
    assert actual.last_sequence_number == Decimal(9)
    assert len(unseen) == 2
    assert unseen[0] == marker1
    assert unseen[1] == marker2
