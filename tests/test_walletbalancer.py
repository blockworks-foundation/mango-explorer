from .context import mango
from .fakes import fake_token

from decimal import Decimal
from solana.publickey import PublicKey


ETH_TOKEN = mango.Token("ETH", "Wrapped Ethereum (Sollet)", PublicKey(
    "2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk"), Decimal(6))
BTC_TOKEN = mango.Token("BTC", "Wrapped Bitcoin (Sollet)", PublicKey(
    "9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E"), Decimal(6))
USDT_TOKEN = mango.Token("USDT", "USDT", PublicKey("Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"), Decimal(6))


def test_target_balance_constructor():
    succeeded = False
    try:
        mango.TargetBalance(fake_token())
    except TypeError:
        # Can't instantiate the abstract base class.
        succeeded = True
    assert succeeded


def test_fixed_target_balance_constructor():
    token = fake_token()
    value = Decimal(23)
    actual = mango.FixedTargetBalance(token, value)
    assert actual is not None
    assert actual.token == token
    assert actual.value == value


def test_percentage_target_balance_constructor():
    token = fake_token()
    value = Decimal(5)
    actual = mango.PercentageTargetBalance(token, value)
    assert actual is not None
    assert actual.token == token
    assert actual.target_fraction == Decimal("0.05")  # Calculated as a fraction instead of a percentage.


def test_target_balance_parser_constructor():
    token1 = fake_token()
    token2 = fake_token()
    tokens = [token1, token2]
    actual = mango.TargetBalanceParser(tokens)
    assert actual is not None
    assert actual.tokens == tokens


def test_calculate_required_balance_changes():
    current_balances = [
        mango.TokenValue(ETH_TOKEN, Decimal("0.5")),
        mango.TokenValue(BTC_TOKEN, Decimal("0.2")),
        mango.TokenValue(USDT_TOKEN, Decimal("10000")),
    ]
    desired_balances = [
        mango.TokenValue(ETH_TOKEN, Decimal("1")),
        mango.TokenValue(BTC_TOKEN, Decimal("0.1"))
    ]

    changes = mango.calculate_required_balance_changes(current_balances, desired_balances)

    assert(changes[0].token.symbol == "ETH")
    assert(changes[0].value == Decimal("0.5"))
    assert(changes[1].token.symbol == "BTC")
    assert(changes[1].value == Decimal("-0.1"))


def test_percentage_target_balance():
    token = fake_token()
    percentage_parsed_balance_change = mango.PercentageTargetBalance(token, Decimal(33))
    assert(percentage_parsed_balance_change.token == token)

    current_token_price = Decimal(2000)  # It's $2,000 per TOKEN
    current_account_value = Decimal(10000)  # We hold $10,000 in total across all assets in our account.
    resolved_parsed_balance_change = percentage_parsed_balance_change.resolve(
        current_token_price, current_account_value)
    assert(resolved_parsed_balance_change.token == token)
    # 33% of $10,000 is $3,300
    # $3,300 spent on TOKEN gives us 1.65 TOKEN
    assert(resolved_parsed_balance_change.value == Decimal("1.65"))


def test_target_balance_parser():
    parser = mango.TargetBalanceParser([ETH_TOKEN, BTC_TOKEN, USDT_TOKEN])
    parsed_percent = parser.parse("eth:10%")
    assert(parsed_percent.token == ETH_TOKEN)
    assert(parsed_percent.target_fraction == Decimal("0.1"))

    parsed_fixed = parser.parse("eth:70")
    assert(parsed_fixed.token == ETH_TOKEN)
    assert(parsed_fixed.value == Decimal(70))


def test_filter_small_changes_constructor():
    current_prices = [
        mango.TokenValue(ETH_TOKEN, Decimal("4000")),
        mango.TokenValue(BTC_TOKEN, Decimal("60000")),
        mango.TokenValue(USDT_TOKEN, Decimal("1")),
    ]
    current_balances = [
        mango.TokenValue(ETH_TOKEN, Decimal("0.5")),
        mango.TokenValue(BTC_TOKEN, Decimal("0.2")),
        mango.TokenValue(USDT_TOKEN, Decimal("10000")),
    ]
    action_threshold = Decimal("0.01")  # Don't bother if it's less than 1% of the total value (24,000)
    expected_prices = {
        f"{current_prices[0].token.mint}": current_prices[0],
        f"{current_prices[1].token.mint}": current_prices[1],
        f"{current_prices[2].token.mint}": current_prices[2]
    }
    expected_total_balance = Decimal(24000)
    expected_action_threshold_value = expected_total_balance / 100  # Action threshold is 0.01
    actual = mango.FilterSmallChanges(action_threshold, current_balances, current_prices)
    assert actual is not None
    assert actual.logger is not None
    assert actual.prices == expected_prices
    assert actual.total_balance == expected_total_balance
    assert actual.action_threshold_value == expected_action_threshold_value


def test_filtering_small_changes():
    current_prices = [
        mango.TokenValue(ETH_TOKEN, Decimal("4000")),
        mango.TokenValue(BTC_TOKEN, Decimal("60000")),
        mango.TokenValue(USDT_TOKEN, Decimal("1")),
    ]
    current_balances = [
        mango.TokenValue(ETH_TOKEN, Decimal("0.5")),
        mango.TokenValue(BTC_TOKEN, Decimal("0.2")),
        mango.TokenValue(USDT_TOKEN, Decimal("10000")),
    ]
    action_threshold = Decimal("0.01")  # Don't bother if it's less than 1% of the total value (24,000)
    actual = mango.FilterSmallChanges(action_threshold, current_balances, current_prices)

    # 0.05 ETH is worth $200 at our test prices, which is less than our $240 threshold
    assert(not actual.allow(mango.TokenValue(ETH_TOKEN, Decimal("0.05"))))

    # 0.05 BTC is worth $3,000 at our test prices, which is much more than our $240 threshold
    assert(actual.allow(mango.TokenValue(BTC_TOKEN, Decimal("0.05"))))


def test_sort_changes_for_trades():
    eth_buy = mango.TokenValue(ETH_TOKEN, Decimal("5"))
    btc_sell = mango.TokenValue(BTC_TOKEN, Decimal("-1"))
    sorted_changes = mango.sort_changes_for_trades([
        eth_buy,
        btc_sell
    ])

    assert(sorted_changes[0] == btc_sell)
    assert(sorted_changes[1] == eth_buy)
