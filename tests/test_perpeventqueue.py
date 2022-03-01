import typing

from solana.publickey import PublicKey

from .context import mango
from .fakes import fake_account_info, fake_seeded_public_key

from decimal import Decimal


def test_constructor() -> None:
    address = fake_seeded_public_key("perp event queue address")
    account_info: mango.AccountInfo = fake_account_info(address)
    meta_data: mango.Metadata = mango.Metadata(
        mango.layouts.DATA_TYPE.EventQueue, mango.Version.V1, True
    )
    head: Decimal = Decimal(0)
    count: Decimal = Decimal(0)
    sequence_number: Decimal = Decimal(0)
    unprocessed_events: typing.Sequence[mango.PerpEvent] = []
    processed_events: typing.Sequence[mango.PerpEvent] = []

    actual = mango.PerpEventQueue(
        account_info,
        mango.Version.V1,
        meta_data,
        mango.NullLotSizeConverter(),
        head,
        count,
        sequence_number,
        unprocessed_events,
        processed_events,
    )
    assert actual is not None
    assert actual.account_info == account_info
    assert actual.meta_data == meta_data
    assert actual.address == address
    assert actual.head == head
    assert actual.count == count
    assert actual.sequence_number == sequence_number
    assert actual.unprocessed_events == unprocessed_events
    assert actual.processed_events == processed_events


def _fake_pev(
    head: Decimal,
    count: Decimal,
    sequence_number: Decimal,
    unprocessed: typing.Sequence[mango.PerpEvent],
    processed: typing.Sequence[mango.PerpEvent],
) -> mango.PerpEventQueue:
    address = fake_seeded_public_key("perp event queue address")
    account_info: mango.AccountInfo = fake_account_info(address)
    meta_data: mango.Metadata = mango.Metadata(
        mango.layouts.DATA_TYPE.EventQueue, mango.Version.V1, True
    )
    return mango.PerpEventQueue(
        account_info,
        mango.Version.V1,
        meta_data,
        mango.NullLotSizeConverter(),
        head,
        count,
        sequence_number,
        unprocessed,
        processed,
    )


class TstPE(mango.PerpEvent):
    def __init__(self, event_type: int = 25, original_index: Decimal = Decimal(0)):
        super().__init__(event_type, original_index)

    @property
    def accounts_to_crank(self) -> typing.Sequence[PublicKey]:
        return []

    def __str__(self) -> str:
        return f"« TstPE [{self.event_type}] »"


class TstFillPE(mango.PerpFillEvent):
    def __init__(
        self, maker: PublicKey, maker_id: int, taker: PublicKey, taker_id: int
    ):
        super().__init__(
            0,
            Decimal(0),
            mango.utc_now(),
            mango.Side.BUY,
            Decimal(1),
            Decimal(1),
            Decimal(1),
            Decimal(1),
            True,
            maker,
            Decimal(maker_id),
            Decimal(0),
            taker,
            Decimal(taker_id),
            Decimal(0),
        )

    def __str__(self) -> str:
        return f"« TstFillPE [{self.maker_order_id} / {self.taker_order_id}] »"


def test_unseen_with_no_changes() -> None:
    initial = _fake_pev(
        Decimal(5),
        Decimal(2),
        Decimal(7),
        [],
        [TstPE(), TstPE(), TstPE(), TstPE(), TstPE()],
    )
    actual: mango.UnseenPerpEventChangesTracker = mango.UnseenPerpEventChangesTracker(
        initial
    )
    assert actual.last_sequence_number == Decimal(7)

    updated = _fake_pev(
        Decimal(5),
        Decimal(2),
        Decimal(7),
        [],
        [TstPE(), TstPE(), TstPE(), TstPE(), TstPE()],
    )
    unseen = actual.unseen(updated)
    assert len(unseen) == 0
    assert actual.last_sequence_number == Decimal(7)


def test_unseen_with_one_unprocessed_change() -> None:
    initial = _fake_pev(
        Decimal(1),
        Decimal(0),
        Decimal(1),
        [TstPE()],
        [TstPE(), TstPE(), TstPE(), TstPE()],
    )
    actual: mango.UnseenPerpEventChangesTracker = mango.UnseenPerpEventChangesTracker(
        initial
    )
    assert actual.last_sequence_number == Decimal(1)

    marker = TstPE(50)
    updated = _fake_pev(
        Decimal(2),
        Decimal(1),
        Decimal(2),
        [marker],
        [TstPE(), TstPE(), TstPE(), TstPE()],
    )
    unseen = actual.unseen(updated)
    assert actual.last_sequence_number == Decimal(2)
    assert len(unseen) == 1
    assert unseen[0] == marker


def test_unseen_with_two_unprocessed_changes() -> None:
    initial = _fake_pev(
        Decimal(1), Decimal(0), Decimal(1), [], [TstPE(), TstPE(), TstPE()]
    )
    actual: mango.UnseenPerpEventChangesTracker = mango.UnseenPerpEventChangesTracker(
        initial
    )
    assert actual.last_sequence_number == Decimal(1)

    marker1 = TstPE(50)
    marker2 = TstPE(51)
    updated = _fake_pev(
        Decimal(3),
        Decimal(2),
        Decimal(3),
        [marker1, marker2],
        [TstPE(), TstPE(), TstPE()],
    )
    unseen = actual.unseen(updated)
    assert actual.last_sequence_number == Decimal(3)
    assert len(unseen) == 2
    assert unseen[0] == marker1
    assert unseen[1] == marker2


def test_unseen_with_two_processed_changes() -> None:
    # This should be identical to the previous test - it shouldn't matter to 'seen' tracking whether an event
    # is processed or not.
    initial = _fake_pev(
        Decimal(1), Decimal(0), Decimal(1), [], [TstPE(), TstPE(), TstPE()]
    )
    actual: mango.UnseenPerpEventChangesTracker = mango.UnseenPerpEventChangesTracker(
        initial
    )
    assert actual.last_sequence_number == Decimal(1)

    marker1 = TstPE(50)
    marker2 = TstPE(51)
    updated = _fake_pev(
        Decimal(3),
        Decimal(0),
        Decimal(3),
        [marker1, marker2],
        [TstPE(), TstPE(), TstPE()],
    )
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
    initial = _fake_pev(
        Decimal(4), Decimal(0), Decimal(7), [], [TstPE(), TstPE(), TstPE()]
    )
    actual: mango.UnseenPerpEventChangesTracker = mango.UnseenPerpEventChangesTracker(
        initial
    )
    assert actual.last_sequence_number == Decimal(7)

    marker1 = TstPE(50)
    marker2 = TstPE(51)
    updated = _fake_pev(
        Decimal(1),
        Decimal(2),
        Decimal(9),
        [marker1, marker2],
        [TstPE(), TstPE(), TstPE()],
    )
    unseen = actual.unseen(updated)
    assert actual.last_sequence_number == Decimal(9)
    assert len(unseen) == 2
    assert unseen[0] == marker1
    assert unseen[1] == marker2


def test_fills_for_account() -> None:
    user1 = fake_seeded_public_key("user1")
    user2 = fake_seeded_public_key("user2")
    user3 = fake_seeded_public_key("user3")
    order1 = TstFillPE(user1, 11, user2, 21)
    order2 = TstFillPE(user2, 12, user3, 22)
    order3 = TstFillPE(user3, 13, user1, 23)
    pev = _fake_pev(Decimal(4), Decimal(0), Decimal(7), [], [order1, order2, order3])

    my_fills = pev.fills_for_account(user1)
    assert len(my_fills) == 2
    assert my_fills[0] == order1
    assert my_fills[1] == order3


def test_no_fills_for_account() -> None:
    user1 = fake_seeded_public_key("user1")
    user2 = fake_seeded_public_key("user2")
    user3 = fake_seeded_public_key("user3")
    user4 = fake_seeded_public_key("user4")
    order1 = TstFillPE(user1, 11, user2, 21)
    order2 = TstFillPE(user2, 12, user3, 22)
    order3 = TstFillPE(user3, 13, user1, 23)
    pev = _fake_pev(Decimal(4), Decimal(0), Decimal(7), [], [order1, order2, order3])

    my_fills = pev.fills_for_account(user4)
    assert len(my_fills) == 0


def test_unseen_fills_for_account() -> None:
    user1 = fake_seeded_public_key("user1")
    user2 = fake_seeded_public_key("user2")
    user3 = fake_seeded_public_key("user3")
    order1 = TstFillPE(user1, 11, user2, 21)
    order2 = TstFillPE(user2, 12, user3, 22)
    order3 = TstFillPE(user3, 13, user1, 23)
    pev1 = _fake_pev(Decimal(4), Decimal(0), Decimal(7), [], [order1, order2, order3])

    actual = mango.UnseenAccountFillEventTracker(pev1, user1)

    order4 = TstFillPE(user3, 14, user2, 24)
    order5 = TstFillPE(user1, 15, user3, 25)
    order6 = TstFillPE(user2, 16, user1, 26)
    pev2 = _fake_pev(
        Decimal(4),
        Decimal(0),
        Decimal(7),
        [],
        [order1, order2, order3, order4, order5, order6],
    )

    my_unseen_fills = actual.unseen(pev2)
    assert len(my_unseen_fills) == 2
    assert my_unseen_fills[0] == order5
    assert my_unseen_fills[1] == order6


def test_no_unseen_fills_for_account() -> None:
    # Exactly the same test as before but with user4 as the account we're watching for.
    user1 = fake_seeded_public_key("user1")
    user2 = fake_seeded_public_key("user2")
    user3 = fake_seeded_public_key("user3")
    user4 = fake_seeded_public_key("user4")
    order1 = TstFillPE(user1, 11, user2, 21)
    order2 = TstFillPE(user2, 12, user3, 22)
    order3 = TstFillPE(user3, 13, user1, 23)
    pev1 = _fake_pev(Decimal(4), Decimal(0), Decimal(7), [], [order1, order2, order3])

    actual = mango.UnseenAccountFillEventTracker(pev1, user4)

    order4 = TstFillPE(user3, 14, user2, 24)
    order5 = TstFillPE(user1, 15, user3, 25)
    order6 = TstFillPE(user2, 16, user1, 26)
    pev2 = _fake_pev(
        Decimal(4),
        Decimal(0),
        Decimal(7),
        [],
        [order1, order2, order3, order4, order5, order6],
    )

    my_unseen_fills = actual.unseen(pev2)
    assert len(my_unseen_fills) == 0


def test_no_changes_in_unseen_fills_for_account() -> None:
    user1 = fake_seeded_public_key("user1")
    user2 = fake_seeded_public_key("user2")
    user3 = fake_seeded_public_key("user3")
    user4 = fake_seeded_public_key("user4")
    order1 = TstFillPE(user1, 11, user2, 21)
    order2 = TstFillPE(user2, 12, user3, 22)
    order3 = TstFillPE(user3, 13, user1, 23)
    pev1 = _fake_pev(Decimal(4), Decimal(0), Decimal(7), [], [order1, order2, order3])

    actual = mango.UnseenAccountFillEventTracker(pev1, user1)

    order4 = TstFillPE(user3, 14, user2, 24)
    order5 = TstFillPE(user4, 15, user3, 25)
    order6 = TstFillPE(user2, 16, user4, 26)
    pev2 = _fake_pev(
        Decimal(4),
        Decimal(0),
        Decimal(7),
        [],
        [order1, order2, order3, order4, order5, order6],
    )

    my_unseen_fills = actual.unseen(pev2)
    assert len(my_unseen_fills) == 0
