from .context import mango

from datetime import timedelta
from decimal import Decimal

from .fakes import fake_seeded_public_key


def __build_initial_order() -> mango.Order:
    owner = fake_seeded_public_key("owner")
    now = mango.local_now()
    initial = mango.Order.from_values(
        id=5,
        client_id=8,
        owner=owner,
        side=mango.Side.SELL,
        price=Decimal(88),
        quantity=Decimal(15),
        order_type=mango.OrderType.POST_ONLY_SLIDE,
        reduce_only=True,
        expiration=now,
        match_limit=6,
    )

    assert initial.id == 5
    assert initial.client_id == 8
    assert initial.owner == owner
    assert initial.side == mango.Side.SELL
    assert initial.price == 88
    assert initial.quantity == 15
    assert initial.order_type == mango.OrderType.POST_ONLY_SLIDE
    assert initial.reduce_only
    assert initial.expiration == now
    assert initial.match_limit == 6

    return initial


def test_from_values_defaults() -> None:
    actual = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(98), quantity=Decimal(20)
    )

    assert actual.id == 0
    assert actual.client_id == 0
    assert actual.owner == mango.SYSTEM_PROGRAM_ADDRESS
    assert actual.side == mango.Side.BUY
    assert actual.price == 98
    assert actual.quantity == 20
    assert actual.order_type == mango.OrderType.UNKNOWN
    assert not actual.reduce_only
    assert actual.expiration == mango.Order.NoExpiration
    assert actual.match_limit == mango.Order.DefaultMatchLimit


def test_from_values_all() -> None:
    owner = fake_seeded_public_key("owner")
    now = mango.local_now()
    actual = mango.Order.from_values(
        id=5,
        client_id=8,
        owner=owner,
        side=mango.Side.SELL,
        price=Decimal(88),
        quantity=Decimal(15),
        order_type=mango.OrderType.POST_ONLY_SLIDE,
        reduce_only=True,
        expiration=now,
        match_limit=6,
    )

    assert actual.id == 5
    assert actual.client_id == 8
    assert actual.owner == owner
    assert actual.side == mango.Side.SELL
    assert actual.price == 88
    assert actual.quantity == 15
    assert actual.order_type == mango.OrderType.POST_ONLY_SLIDE
    assert actual.reduce_only
    assert actual.expiration == now
    assert actual.match_limit == 6


def test_with_update_id() -> None:
    initial = __build_initial_order()
    initial_owner = initial.owner
    initial_expiration = initial.expiration

    actual = initial.with_update(id=7)
    assert actual.id == 7  # Changed!
    assert actual.client_id == 8
    assert actual.owner == initial_owner
    assert actual.side == mango.Side.SELL
    assert actual.price == 88
    assert actual.quantity == 15
    assert actual.order_type == mango.OrderType.POST_ONLY_SLIDE
    assert actual.reduce_only
    assert actual.expiration == initial_expiration
    assert actual.match_limit == 6


def test_with_update_client_id() -> None:
    initial = __build_initial_order()
    initial_owner = initial.owner
    initial_expiration = initial.expiration

    actual = initial.with_update(client_id=7)
    assert actual.id == 5
    assert actual.client_id == 7  # Changed!
    assert actual.owner == initial_owner
    assert actual.side == mango.Side.SELL
    assert actual.price == 88
    assert actual.quantity == 15
    assert actual.order_type == mango.OrderType.POST_ONLY_SLIDE
    assert actual.reduce_only
    assert actual.expiration == initial_expiration
    assert actual.match_limit == 6


def test_with_update_owner() -> None:
    initial = __build_initial_order()
    initial_expiration = initial.expiration

    updated_owner = fake_seeded_public_key("new owner")
    actual = initial.with_update(owner=updated_owner)
    assert actual.id == 5
    assert actual.client_id == 8
    assert actual.owner == updated_owner  # Changed!
    assert actual.side == mango.Side.SELL
    assert actual.price == 88
    assert actual.quantity == 15
    assert actual.order_type == mango.OrderType.POST_ONLY_SLIDE
    assert actual.reduce_only
    assert actual.expiration == initial_expiration
    assert actual.match_limit == 6


def test_with_update_side() -> None:
    initial = __build_initial_order()
    initial_owner = initial.owner
    initial_expiration = initial.expiration

    actual = initial.with_update(side=mango.Side.BUY)
    assert actual.id == 5
    assert actual.client_id == 8
    assert actual.owner == initial_owner
    assert actual.side == mango.Side.BUY  # Changed!
    assert actual.price == 88
    assert actual.quantity == 15
    assert actual.order_type == mango.OrderType.POST_ONLY_SLIDE
    assert actual.reduce_only
    assert actual.expiration == initial_expiration
    assert actual.match_limit == 6


def test_with_update_price() -> None:
    initial = __build_initial_order()
    initial_owner = initial.owner
    initial_expiration = initial.expiration

    actual = initial.with_update(price=Decimal(25))
    assert actual.id == 5
    assert actual.client_id == 8
    assert actual.owner == initial_owner
    assert actual.side == mango.Side.SELL
    assert actual.price == 25  # Changed!
    assert actual.quantity == 15
    assert actual.order_type == mango.OrderType.POST_ONLY_SLIDE
    assert actual.reduce_only
    assert actual.expiration == initial_expiration
    assert actual.match_limit == 6


def test_with_update_quantity() -> None:
    initial = __build_initial_order()
    initial_owner = initial.owner
    initial_expiration = initial.expiration

    actual = initial.with_update(quantity=Decimal(17))
    assert actual.id == 5
    assert actual.client_id == 8
    assert actual.owner == initial_owner
    assert actual.side == mango.Side.SELL
    assert actual.price == 88
    assert actual.quantity == 17  # Changed!
    assert actual.order_type == mango.OrderType.POST_ONLY_SLIDE
    assert actual.reduce_only
    assert actual.expiration == initial_expiration
    assert actual.match_limit == 6


def test_with_update_order_type() -> None:
    initial = __build_initial_order()
    initial_owner = initial.owner
    initial_expiration = initial.expiration

    actual = initial.with_update(order_type=mango.OrderType.MARKET)
    assert actual.id == 5
    assert actual.client_id == 8
    assert actual.owner == initial_owner
    assert actual.side == mango.Side.SELL
    assert actual.price == 88
    assert actual.quantity == 15
    assert actual.order_type == mango.OrderType.MARKET  # Changed!
    assert actual.reduce_only
    assert actual.expiration == initial_expiration
    assert actual.match_limit == 6


def test_with_update_reduce_only() -> None:
    initial = __build_initial_order()
    initial_owner = initial.owner
    initial_expiration = initial.expiration

    actual = initial.with_update(reduce_only=False)
    assert actual.id == 5
    assert actual.client_id == 8
    assert actual.owner == initial_owner
    assert actual.side == mango.Side.SELL
    assert actual.price == 88
    assert actual.quantity == 15
    assert actual.order_type == mango.OrderType.POST_ONLY_SLIDE
    assert not actual.reduce_only  # Changed!
    assert actual.expiration == initial_expiration
    assert actual.match_limit == 6


def test_with_update_expiration() -> None:
    initial = __build_initial_order()
    initial_owner = initial.owner

    updated_expiration = mango.local_now() + timedelta(seconds=10)
    actual = initial.with_update(expiration=updated_expiration)
    assert actual.id == 5
    assert actual.client_id == 8
    assert actual.owner == initial_owner
    assert actual.side == mango.Side.SELL
    assert actual.price == 88
    assert actual.quantity == 15
    assert actual.order_type == mango.OrderType.POST_ONLY_SLIDE
    assert actual.reduce_only
    assert actual.expiration == updated_expiration  # Changed!
    assert actual.match_limit == 6


def test_with_update_match_limit() -> None:
    initial = __build_initial_order()
    initial_owner = initial.owner
    initial_expiration = initial.expiration

    actual = initial.with_update(match_limit=14)
    assert actual.id == 5
    assert actual.client_id == 8
    assert actual.owner == initial_owner
    assert actual.side == mango.Side.SELL
    assert actual.price == 88
    assert actual.quantity == 15
    assert actual.order_type == mango.OrderType.POST_ONLY_SLIDE
    assert actual.reduce_only
    assert actual.expiration == initial_expiration
    assert actual.match_limit == 14  # Changed!


def test_with_update_all() -> None:
    initial = __build_initial_order()
    updated_owner = fake_seeded_public_key("new owner")
    updated_expiration = mango.local_now() + timedelta(seconds=15)
    actual = initial.with_update(
        id=9,
        client_id=17,
        owner=updated_owner,
        side=mango.Side.BUY,
        price=Decimal(52),
        quantity=Decimal(26),
        order_type=mango.OrderType.POST_ONLY,
        reduce_only=False,
        expiration=updated_expiration,
        match_limit=11,
    )
    assert actual.id == 9
    assert actual.client_id == 17
    assert actual.owner == updated_owner
    assert actual.side == mango.Side.BUY
    assert actual.price == 52
    assert actual.quantity == 26
    assert actual.order_type == mango.OrderType.POST_ONLY
    assert not actual.reduce_only
    assert actual.expiration == updated_expiration
    assert actual.match_limit == 11


def test_order_expired() -> None:
    actual = mango.Order.from_values(
        side=mango.Side.BUY,
        price=Decimal(10),
        quantity=Decimal(20),
        order_type=mango.OrderType.LIMIT,
        expiration=mango.utc_now() - timedelta(seconds=1),
    )

    assert actual.expired


def test_order_not_expired() -> None:
    actual = mango.Order.from_values(
        side=mango.Side.BUY,
        price=Decimal(10),
        quantity=Decimal(20),
        order_type=mango.OrderType.LIMIT,
        expiration=mango.utc_now() + timedelta(seconds=5),
    )

    assert not actual.expired
