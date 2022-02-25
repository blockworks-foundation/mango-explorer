import mango

from datetime import timedelta
from decimal import Decimal
from mango.marketmaking.toleranceorderreconciler import ToleranceOrderReconciler

from ..fakes import fake_model_state


def test_buy_does_not_match_sell() -> None:
    actual = ToleranceOrderReconciler(Decimal(1), Decimal(1), timedelta(seconds=0))
    existing = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10)
    )
    desired = mango.Order.from_values(
        mango.Side.SELL, price=Decimal(1), quantity=Decimal(10)
    )

    assert not actual.is_within_tolderance(existing, desired)


def test_exact_match_with_small_tolerance_matches() -> None:
    actual = ToleranceOrderReconciler(
        Decimal("0.001"), Decimal("0.001"), timedelta(seconds=0)
    )
    existing = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10)
    )
    desired = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10)
    )

    assert actual.is_within_tolderance(existing, desired)


def test_exact_match_with_zero_tolerance_matches() -> None:
    actual = ToleranceOrderReconciler(Decimal(0), Decimal(0), timedelta(seconds=0))
    existing = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10)
    )
    desired = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10)
    )

    assert actual.is_within_tolderance(existing, desired)


def test_quantity_within_positive_tolerance_matches() -> None:
    actual = ToleranceOrderReconciler(
        Decimal(0), Decimal("0.001"), timedelta(seconds=0)
    )
    existing = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10)
    )
    desired = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal("10.009")
    )

    assert actual.is_within_tolderance(existing, desired)


def test_quantity_positive_tolerance_boundary_matches() -> None:
    actual = ToleranceOrderReconciler(
        Decimal(0), Decimal("0.001"), timedelta(seconds=0)
    )
    existing = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10)
    )
    desired = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal("10.01")
    )

    assert actual.is_within_tolderance(existing, desired)


def test_quantity_outside_positive_tolerance_no_match() -> None:
    actual = ToleranceOrderReconciler(
        Decimal(0), Decimal("0.001"), timedelta(seconds=0)
    )
    existing = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10)
    )
    desired = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal("10.011")
    )

    assert not actual.is_within_tolderance(existing, desired)


def test_quantity_within_negative_tolerance_matches() -> None:
    actual = ToleranceOrderReconciler(
        Decimal(0), Decimal("0.001"), timedelta(seconds=0)
    )
    existing = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10)
    )
    desired = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal("9.991")
    )

    assert actual.is_within_tolderance(existing, desired)


def test_quantity_negative_tolerance_boundary_matches() -> None:
    actual = ToleranceOrderReconciler(
        Decimal(0), Decimal("0.001"), timedelta(seconds=0)
    )
    existing = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10)
    )
    desired = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal("9.99")
    )

    assert actual.is_within_tolderance(existing, desired)


def test_quantity_outside_negative_tolerance_no_match() -> None:
    actual = ToleranceOrderReconciler(
        Decimal(0), Decimal("0.001"), timedelta(seconds=0)
    )
    existing = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10)
    )
    desired = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal("9.989")
    )

    assert not actual.is_within_tolderance(existing, desired)


def test_price_within_positive_tolerance_matches() -> None:
    actual = ToleranceOrderReconciler(
        Decimal("0.001"), Decimal(0), timedelta(seconds=0)
    )
    existing = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10)
    )
    desired = mango.Order.from_values(
        mango.Side.BUY, price=Decimal("1.0009"), quantity=Decimal(10)
    )

    assert actual.is_within_tolderance(existing, desired)


def test_price_positive_tolerance_boundary_matches() -> None:
    actual = ToleranceOrderReconciler(
        Decimal("0.001"), Decimal(0), timedelta(seconds=0)
    )
    existing = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10)
    )
    desired = mango.Order.from_values(
        mango.Side.BUY, price=Decimal("1.001"), quantity=Decimal(10)
    )

    assert actual.is_within_tolderance(existing, desired)


def test_price_outside_positive_tolerance_no_match() -> None:
    actual = ToleranceOrderReconciler(
        Decimal("0.001"), Decimal(0), timedelta(seconds=0)
    )
    existing = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10)
    )
    desired = mango.Order.from_values(
        mango.Side.BUY, price=Decimal("1.0011"), quantity=Decimal(10)
    )

    assert not actual.is_within_tolderance(existing, desired)


def test_price_within_negative_tolerance_matches() -> None:
    actual = ToleranceOrderReconciler(
        Decimal("0.001"), Decimal(0), timedelta(seconds=0)
    )
    existing = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10)
    )
    desired = mango.Order.from_values(
        mango.Side.BUY, price=Decimal("0.9991"), quantity=Decimal(10)
    )

    assert actual.is_within_tolderance(existing, desired)


def test_price_negative_tolerance_boundary_matches() -> None:
    actual = ToleranceOrderReconciler(
        Decimal("0.001"), Decimal(0), timedelta(seconds=0)
    )
    existing = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10)
    )
    desired = mango.Order.from_values(
        mango.Side.BUY, price=Decimal("0.999"), quantity=Decimal(10)
    )

    assert actual.is_within_tolderance(existing, desired)


def test_price_outside_negative_tolerance_no_match() -> None:
    actual = ToleranceOrderReconciler(
        Decimal("0.001"), Decimal(0), timedelta(seconds=0)
    )
    existing = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10)
    )
    desired = mango.Order.from_values(
        mango.Side.BUY, price=Decimal("0.9989"), quantity=Decimal(10)
    )

    assert not actual.is_within_tolderance(existing, desired)


def test_time_in_force_early_match() -> None:
    now = mango.utc_now()
    actual = ToleranceOrderReconciler(
        Decimal("0.001"), Decimal(0), timedelta(seconds=5)
    )
    existing = mango.Order.from_values(
        mango.Side.BUY,
        price=Decimal(1),
        quantity=Decimal(10),
        expiration=now - timedelta(seconds=3),
    )
    desired = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10), expiration=now
    )

    assert actual.is_within_tolderance(existing, desired)


def test_time_in_force_too_early_no_match() -> None:
    now = mango.utc_now()
    actual = ToleranceOrderReconciler(
        Decimal("0.001"), Decimal(0), timedelta(seconds=5)
    )
    existing = mango.Order.from_values(
        mango.Side.BUY,
        price=Decimal(1),
        quantity=Decimal(10),
        expiration=now - timedelta(seconds=6),
    )
    desired = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10), expiration=now
    )

    assert not actual.is_within_tolderance(existing, desired)


def test_time_in_force_late_match() -> None:
    now = mango.utc_now()
    actual = ToleranceOrderReconciler(
        Decimal("0.001"), Decimal(0), timedelta(seconds=5)
    )
    existing = mango.Order.from_values(
        mango.Side.BUY,
        price=Decimal(1),
        quantity=Decimal(10),
        expiration=now + timedelta(seconds=3),
    )
    desired = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10), expiration=now
    )

    assert actual.is_within_tolderance(existing, desired)


def test_time_in_force_too_late_no_match() -> None:
    now = mango.utc_now()
    actual = ToleranceOrderReconciler(
        Decimal("0.001"), Decimal(0), timedelta(seconds=5)
    )
    existing = mango.Order.from_values(
        mango.Side.BUY,
        price=Decimal(1),
        quantity=Decimal(10),
        expiration=now + timedelta(seconds=6),
    )
    desired = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10), expiration=now
    )

    assert not actual.is_within_tolderance(existing, desired)


def test_reconcile_no_acceptable_orders() -> None:
    existing = [
        mango.Order.from_values(
            mango.Side.BUY, price=Decimal(99), quantity=Decimal(10)
        ),
        mango.Order.from_values(
            mango.Side.SELL, price=Decimal(101), quantity=Decimal(10)
        ),
    ]
    desired = [
        mango.Order.from_values(
            mango.Side.BUY, price=Decimal(100), quantity=Decimal(10)
        ),
        mango.Order.from_values(
            mango.Side.SELL, price=Decimal(102), quantity=Decimal(10)
        ),
    ]
    model_state = fake_model_state()
    actual = ToleranceOrderReconciler(
        Decimal("0.001"), Decimal("0.001"), timedelta(seconds=0)
    )
    result = actual.reconcile(model_state, existing, desired)

    assert result.to_place == desired
    assert result.to_cancel == existing
    assert result.to_keep == []
    assert result.to_ignore == []


def test_reconcile_all_acceptable_orders() -> None:
    existing = [
        mango.Order.from_values(
            mango.Side.BUY, price=Decimal(99), quantity=Decimal(10)
        ),
        mango.Order.from_values(
            mango.Side.SELL, price=Decimal(101), quantity=Decimal(10)
        ),
    ]
    desired = [
        mango.Order.from_values(
            mango.Side.BUY, price=Decimal("99.01"), quantity=Decimal(10)
        ),
        mango.Order.from_values(
            mango.Side.SELL, price=Decimal("101.01"), quantity=Decimal(10)
        ),
    ]
    model_state = fake_model_state()
    actual = ToleranceOrderReconciler(
        Decimal("0.001"), Decimal("0.001"), timedelta(seconds=0)
    )
    result = actual.reconcile(model_state, existing, desired)

    assert result.to_place == []
    assert result.to_cancel == []
    assert result.to_keep == existing
    assert result.to_ignore == desired


def test_reconcile_different_list_sizes_orders() -> None:
    existing = [
        mango.Order.from_values(
            mango.Side.BUY, price=Decimal(98), quantity=Decimal(20)
        ),
        mango.Order.from_values(
            mango.Side.BUY, price=Decimal(99), quantity=Decimal(10)
        ),
        mango.Order.from_values(
            mango.Side.SELL, price=Decimal(101), quantity=Decimal(10)
        ),
        mango.Order.from_values(
            mango.Side.SELL, price=Decimal(102), quantity=Decimal(20)
        ),
    ]
    desired = [
        mango.Order.from_values(
            mango.Side.BUY, price=Decimal("99.01"), quantity=Decimal(10)
        ),
        mango.Order.from_values(
            mango.Side.SELL, price=Decimal("101.01"), quantity=Decimal(10)
        ),
    ]
    model_state = fake_model_state()
    actual = ToleranceOrderReconciler(
        Decimal("0.001"), Decimal("0.001"), timedelta(seconds=0)
    )
    result = actual.reconcile(model_state, existing, desired)

    assert result.to_place == []
    assert len(result.to_cancel) == 2
    assert result.to_cancel[0] == existing[0]
    assert result.to_cancel[1] == existing[3]
    assert len(result.to_keep) == 2
    assert result.to_keep[0] == existing[1]
    assert result.to_keep[1] == existing[2]
    assert result.to_ignore == desired


def test_reconcile_two_acceptable_two_unacceptable_orders() -> None:
    existing = [
        mango.Order.from_values(
            mango.Side.BUY, price=Decimal(98), quantity=Decimal(20)
        ),
        mango.Order.from_values(
            mango.Side.BUY, price=Decimal(99), quantity=Decimal(10)
        ),
        mango.Order.from_values(
            mango.Side.SELL, price=Decimal(101), quantity=Decimal(10)
        ),
        mango.Order.from_values(
            mango.Side.SELL, price=Decimal(102), quantity=Decimal(20)
        ),
    ]
    desired = [
        mango.Order.from_values(
            mango.Side.BUY, price=Decimal("98.1"), quantity=Decimal(20)
        ),
        mango.Order.from_values(
            mango.Side.BUY, price=Decimal("99.01"), quantity=Decimal(10)
        ),
        mango.Order.from_values(
            mango.Side.SELL, price=Decimal("101.01"), quantity=Decimal(10)
        ),
        mango.Order.from_values(
            mango.Side.SELL, price=Decimal("102.11"), quantity=Decimal(20)
        ),
    ]
    model_state = fake_model_state()
    actual = ToleranceOrderReconciler(
        Decimal("0.001"), Decimal("0.001"), timedelta(seconds=0)
    )
    result = actual.reconcile(model_state, existing, desired)

    assert len(result.to_place) == 2
    assert len(result.to_cancel) == 2
    assert len(result.to_keep) == 2
    assert len(result.to_ignore) == 2

    # Desired 1 outcomes
    assert result.to_place[0] == desired[0]
    assert result.to_cancel[0] == existing[0]

    # Desired 2 outcomes
    assert result.to_keep[0] == existing[1]
    assert result.to_ignore[0] == desired[1]

    # Desired 3 outcomes
    assert result.to_keep[1] == existing[2]
    assert result.to_ignore[1] == desired[2]

    # Desired 4 outcomes
    assert result.to_place[1] == desired[3]
    assert result.to_cancel[1] == existing[3]
