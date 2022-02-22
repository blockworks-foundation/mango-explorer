from .context import mango
from .data import load_root_bank, load_node_bank
from .fakes import fake_account_info, fake_context, fake_seeded_public_key, fake_token

from datetime import datetime, timezone
from decimal import Decimal
from solana.publickey import PublicKey


def test_node_bank_constructor() -> None:
    account_info = fake_account_info(fake_seeded_public_key("node bank"))
    meta_data = mango.Metadata(
        mango.layouts.DATA_TYPE.parse(bytearray(b"\x03")), mango.Version.V1, True
    )
    deposits = Decimal(1000)
    borrows = Decimal(100)
    balances = mango.BankBalances(deposits=deposits, borrows=borrows)
    vault = fake_seeded_public_key("vault")

    actual = mango.NodeBank(account_info, mango.Version.V1, meta_data, vault, balances)
    assert actual is not None
    assert actual.account_info == account_info
    assert actual.address == fake_seeded_public_key("node bank")
    assert actual.meta_data == meta_data
    assert actual.meta_data.data_type == mango.layouts.DATA_TYPE.NodeBank
    assert actual.balances.deposits == deposits
    assert actual.balances.borrows == borrows
    assert actual.vault == fake_seeded_public_key("vault")


def test_root_bank_constructor() -> None:
    account_info = fake_account_info(fake_seeded_public_key("root bank"))
    meta_data = mango.Metadata(
        mango.layouts.DATA_TYPE.parse(bytearray(b"\x02")), mango.Version.V1, True
    )
    optimal_util = Decimal("0.7")
    optimal_rate = Decimal("0.06")
    max_rate = Decimal("1.5")
    node_bank = fake_seeded_public_key("node bank")
    deposit_index = Decimal(98765)
    borrow_index = Decimal(12345)
    timestamp = mango.utc_now()

    actual = mango.RootBank(
        account_info,
        mango.Version.V1,
        meta_data,
        optimal_util,
        optimal_rate,
        max_rate,
        [node_bank],
        deposit_index,
        borrow_index,
        timestamp,
    )
    assert actual is not None
    assert actual.account_info == account_info
    assert actual.address == fake_seeded_public_key("root bank")
    assert actual.meta_data == meta_data
    assert actual.meta_data.data_type == mango.layouts.DATA_TYPE.RootBank
    assert actual.optimal_util == optimal_util
    assert actual.optimal_rate == optimal_rate
    assert actual.max_rate == max_rate
    assert actual.node_banks[0] == node_bank
    assert actual.deposit_index == deposit_index
    assert actual.borrow_index == borrow_index
    assert actual.last_updated == timestamp


def test_token_bank_constructor() -> None:
    token = fake_token()
    root_bank_address = fake_seeded_public_key("root bank address")
    actual = mango.TokenBank(token, root_bank_address)

    assert actual is not None
    assert actual.token == token
    assert actual.root_bank_address == root_bank_address


def test_load_root_bank() -> None:
    actual = load_root_bank("tests/testdata/1deposit/root_bank0.json")

    assert actual is not None
    assert actual.address == PublicKey("HUBX4iwWEUK5VrXXXcB7uhuKrfT4fpu2T9iZbg712JrN")
    assert actual.meta_data.version == mango.Version.V1
    assert actual.meta_data.data_type == mango.layouts.DATA_TYPE.RootBank
    assert actual.meta_data.is_initialized
    assert actual.optimal_util == Decimal("0.69999999999999928946")
    assert actual.optimal_rate == Decimal("0.05999999999999872102")
    assert actual.max_rate == Decimal("1.5")
    assert actual.node_banks[0] == PublicKey(
        "J2Lmnc1e4frMnBEJARPoHtfpcohLfN67HdK1inXjTFSM"
    )
    assert actual.deposit_index == Decimal("1000154.42276607355830719825")
    assert actual.borrow_index == Decimal("1000219.00867863010088498754")
    assert actual.last_updated == datetime(2021, 10, 4, 14, 58, 5, 0, timezone.utc)


def test_btc_token_bank() -> None:
    btc = mango.Token(
        "BTC",
        "Wrapped Bitcoin (Sollet)",
        Decimal(6),
        PublicKey("9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E"),
    )

    root_bank = load_root_bank("tests/testdata/tokenbank/btc_root_bank.json")
    node_bank = load_node_bank("tests/testdata/tokenbank/btc_node_bank.json")

    actual = mango.TokenBank(btc, root_bank.address)
    actual.loaded_root_bank = root_bank
    root_bank.loaded_node_banks = [node_bank]

    context = fake_context()
    interest_rates = actual.fetch_interest_rates(context)

    # Typescript says:                        0.00074328994922723268
    assert interest_rates.deposit == Decimal(
        "0.000743289949230430278650314704786385301"
    )
    # Typescript says:                       0.0060962691428017024
    assert interest_rates.borrow == Decimal("0.00609626914280543412386251743252599320")
    assert str(interest_rates) == "« InterestRates Deposit: 0.07% Borrow: 0.61% »"


def test_usdc_token_bank() -> None:
    usdc = mango.Token(
        "USDC",
        "USD Coin",
        Decimal(6),
        PublicKey("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"),
    )

    root_bank = load_root_bank("tests/testdata/tokenbank/usdc_root_bank.json")
    node_bank = load_node_bank("tests/testdata/tokenbank/usdc_node_bank.json")

    actual = mango.TokenBank(usdc, root_bank.address)
    actual.loaded_root_bank = root_bank
    root_bank.loaded_node_banks = [node_bank]

    context = fake_context()
    interest_rates = actual.fetch_interest_rates(context)

    # UI says: 16.94%	23.15%
    # Typescript says:                        0.16874409787690680673
    assert interest_rates.deposit == Decimal("0.168744097876912914047144162858900625")
    # Typescript says:                        0.23058349895659091544
    assert interest_rates.borrow == Decimal("0.230583498956594527437928647548223725")
    assert str(interest_rates) == "« InterestRates Deposit: 16.87% Borrow: 23.06% »"
