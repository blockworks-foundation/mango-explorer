from ..fakes import fake_context
from ..data import load_data_from_directory

from decimal import Decimal
from mango.calculators.healthcalculator import HealthType, HealthCalculator


def test_empty():
    context = fake_context()
    group, cache, account, open_orders = load_data_from_directory("tests/testdata/empty")

    actual = HealthCalculator(context, HealthType.INITIAL)
    health = actual.calculate(account, open_orders, group, cache)
    # Typescript says: 0
    assert health == Decimal("0")


def test_perp_account_no_spot_openorders():
    context = fake_context()
    group, cache, account, open_orders = load_data_from_directory("tests/testdata/perp_account_no_spot_openorders")

    actual = HealthCalculator(context, HealthType.INITIAL)
    health = actual.calculate(account, open_orders, group, cache)
    # Typescript says: 341025333625.51856223547208912805
    # TODO: This is significantly different from Typescript answer
    assert health == Decimal("358923.807024760000053942349040880810")


def test_perp_account_no_spot_openorders_unhealthy():
    context = fake_context()
    group, cache, account, open_orders = load_data_from_directory(
        "tests/testdata/perp_account_no_spot_openorders_unhealthy")

    actual = HealthCalculator(context, HealthType.INITIAL)
    health = actual.calculate(account, open_orders, group, cache)
    # Typescript says: -848086876487.04950427436299875694
    # TODO: This is significantly different from Typescript answer
    assert health == Decimal("-183567.651235339999859541052273925740")


def test_account1():
    context = fake_context()
    group, cache, account, open_orders = load_data_from_directory("tests/testdata/account1")

    actual = HealthCalculator(context, HealthType.INITIAL)
    health = actual.calculate(account, open_orders, group, cache)
    # Typescript says: 454884281.15520619643754685058
    # TODO: This is slightly different from Typescript answer
    assert health == Decimal("455.035346700961950901638175537300417")


def test_account2():
    context = fake_context()
    group, cache, account, open_orders = load_data_from_directory("tests/testdata/account2")

    actual = HealthCalculator(context, HealthType.INITIAL)
    health = actual.calculate(account, open_orders, group, cache)
    # Typescript says: 7516159604.84918334545095675026
    # TODO: This is slightly different from Typescript answer
    assert health == Decimal("7518.40764303100646658275181266617450")
