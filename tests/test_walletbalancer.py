from .context import mango
from .fakes import fake_token

from decimal import Decimal
from solana.publickey import PublicKey


ETH_TOKEN = mango.Token(
    "ETH",
    "Wrapped Ethereum (Sollet)",
    Decimal(6),
    PublicKey("2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk"),
)
BTC_TOKEN = mango.Token(
    "BTC",
    "Wrapped Bitcoin (Sollet)",
    Decimal(6),
    PublicKey("9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E"),
)
USDT_TOKEN = mango.Token(
    "USDT",
    "USDT",
    Decimal(6),
    PublicKey("Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"),
)


def test_target_balance_constructor() -> None:
    succeeded = False
    try:
        mango.TargetBalance("ETH:20")  # type: ignore[abstract]
    except TypeError:
        # Can't instantiate the abstract base class.
        succeeded = True
    assert succeeded


def test_fixed_target_balance_constructor() -> None:
    token = fake_token()
    value = Decimal(23)
    actual = mango.FixedTargetBalance(token.symbol, value)
    assert actual is not None
    assert actual.symbol == token.symbol
    assert actual.value == value


def test_percentage_target_balance_constructor() -> None:
    token = fake_token()
    value = Decimal(5)
    actual = mango.PercentageTargetBalance(token.symbol, value)
    assert actual is not None
    assert actual.symbol == token.symbol
    assert actual.target_fraction == Decimal(
        "0.05"
    )  # Calculated as a fraction instead of a percentage.


def test_calculate_required_balance_changes() -> None:
    current_balances = [
        mango.InstrumentValue(ETH_TOKEN, Decimal("0.5")),
        mango.InstrumentValue(BTC_TOKEN, Decimal("0.2")),
        mango.InstrumentValue(USDT_TOKEN, Decimal("10000")),
    ]
    desired_balances = [
        mango.InstrumentValue(ETH_TOKEN, Decimal("1")),
        mango.InstrumentValue(BTC_TOKEN, Decimal("0.1")),
    ]

    changes = mango.calculate_required_balance_changes(
        current_balances, desired_balances
    )

    assert changes[0].token.symbol == "ETH"
    assert changes[0].value == Decimal("0.5")
    assert changes[1].token.symbol == "BTC"
    assert changes[1].value == Decimal("-0.1")


def test_percentage_target_balance() -> None:
    token = fake_token()
    percentage_parsed_balance_change = mango.PercentageTargetBalance(
        token.symbol, Decimal(33)
    )
    assert percentage_parsed_balance_change.symbol == token.symbol

    current_token_price = Decimal(2000)  # It's $2,000 per TOKEN
    current_account_value = Decimal(
        10000
    )  # We hold $10,000 in total across all assets in our account.
    resolved_parsed_balance_change = percentage_parsed_balance_change.resolve(
        token, current_token_price, current_account_value
    )
    assert resolved_parsed_balance_change.token == token
    # 33% of $10,000 is $3,300
    # $3,300 spent on TOKEN gives us 1.65 TOKEN
    assert resolved_parsed_balance_change.value == Decimal("1.65")


def test_target_balance_parser_fixedvalue() -> None:
    parsed = mango.parse_target_balance("eth:70")
    assert isinstance(parsed, mango.FixedTargetBalance)
    assert (
        parsed.symbol == "eth"
    )  # Case is preserved but comparisons should be case-insensitive
    assert parsed.value == Decimal(70)


def test_target_balance_parser_percentagevalue() -> None:
    parsed = mango.parse_target_balance("btc:10%")
    assert isinstance(parsed, mango.PercentageTargetBalance)
    assert (
        parsed.symbol == "btc"
    )  # Case is preserved but comparisons should be case-insensitive
    assert parsed.target_fraction == Decimal("0.1")


def test_filter_small_changes_constructor() -> None:
    current_prices = [
        mango.InstrumentValue(ETH_TOKEN, Decimal("4000")),
        mango.InstrumentValue(BTC_TOKEN, Decimal("60000")),
        mango.InstrumentValue(USDT_TOKEN, Decimal("1")),
    ]
    current_balances = [
        mango.InstrumentValue(ETH_TOKEN, Decimal("0.5")),
        mango.InstrumentValue(BTC_TOKEN, Decimal("0.2")),
        mango.InstrumentValue(USDT_TOKEN, Decimal("10000")),
    ]
    action_threshold = Decimal(
        "0.01"
    )  # Don't bother if it's less than 1% of the total value (24,000)
    expected_prices = {
        current_prices[0].token.symbol: current_prices[0],
        current_prices[1].token.symbol: current_prices[1],
        current_prices[2].token.symbol: current_prices[2],
    }
    expected_total_balance = Decimal(24000)
    expected_action_threshold_value = (
        expected_total_balance / 100
    )  # Action threshold is 0.01
    actual = mango.FilterSmallChanges(
        action_threshold, current_balances, current_prices
    )
    assert actual is not None
    assert actual.prices == expected_prices
    assert actual.total_balance == expected_total_balance
    assert actual.action_threshold_value == expected_action_threshold_value


def test_filtering_small_changes() -> None:
    current_prices = [
        mango.InstrumentValue(ETH_TOKEN, Decimal("4000")),
        mango.InstrumentValue(BTC_TOKEN, Decimal("60000")),
        mango.InstrumentValue(USDT_TOKEN, Decimal("1")),
    ]
    current_balances = [
        mango.InstrumentValue(ETH_TOKEN, Decimal("0.5")),
        mango.InstrumentValue(BTC_TOKEN, Decimal("0.2")),
        mango.InstrumentValue(USDT_TOKEN, Decimal("10000")),
    ]
    action_threshold = Decimal(
        "0.01"
    )  # Don't bother if it's less than 1% of the total value (24,000)
    actual = mango.FilterSmallChanges(
        action_threshold, current_balances, current_prices
    )

    # 0.05 ETH is worth $200 at our test prices, which is less than our $240 threshold
    assert not actual.allow(mango.InstrumentValue(ETH_TOKEN, Decimal("0.05")))

    # 0.05 BTC is worth $3,000 at our test prices, which is much more than our $240 threshold
    assert actual.allow(mango.InstrumentValue(BTC_TOKEN, Decimal("0.05")))


def test_sort_changes_for_trades() -> None:
    eth_buy = mango.InstrumentValue(ETH_TOKEN, Decimal("5"))
    btc_sell = mango.InstrumentValue(BTC_TOKEN, Decimal("-1"))
    sorted_changes = mango.sort_changes_for_trades([eth_buy, btc_sell])

    assert sorted_changes[0] == btc_sell
    assert sorted_changes[1] == eth_buy
