from .context import mango

from decimal import Decimal

from .fakes import fake_token


def test_round_base_btc() -> None:
    fake_base = fake_token("BTC")
    fake_quote = fake_token("USDC")
    # From BTC/USDC on Mango spot:
    #  « 𝙻𝚘𝚝𝚂𝚒𝚣𝚎𝙲𝚘𝚗𝚟𝚎𝚛𝚝𝚎𝚛 BTC/USDC [base lot size: 100 (6 decimals), quote lot size: 10 (6 decimals)] »
    sut = mango.LotSizeConverter(fake_base, Decimal(100), fake_quote, Decimal(10))
    actual = sut.round_base(Decimal("1234567890.1234567890"))
    assert actual == Decimal("1234567890.1235")


def test_round_base_eth() -> None:
    fake_base = fake_token("ETH")
    fake_quote = fake_token("USDC")
    # From ETH/USDC on Mango spot:
    #  « 𝙻𝚘𝚝𝚂𝚒𝚣𝚎𝙲𝚘𝚗𝚟𝚎𝚛𝚝𝚎𝚛 ETH/USDC [base lot size: 1000 (6 decimals), quote lot size: 10 (6 decimals)] »
    sut = mango.LotSizeConverter(fake_base, Decimal(1000), fake_quote, Decimal(10))
    actual = sut.round_base(Decimal("1234567890.1234567890"))
    assert actual == Decimal("1234567890.123")


def test_round_base_mngo() -> None:
    fake_base = fake_token("MNGO")
    fake_quote = fake_token("USDC")
    # From USDT/USDC on Mango spot:
    #  « 𝙻𝚘𝚝𝚂𝚒𝚣𝚎𝙲𝚘𝚗𝚟𝚎𝚛𝚝𝚎𝚛 MNGO/USDC [base lot size: 1000000 (6 decimals), quote lot size: 100 (6 decimals)] »
    sut = mango.LotSizeConverter(fake_base, Decimal(1000000), fake_quote, Decimal(100))
    actual = sut.round_base(Decimal("1234567890.1234567890"))
    assert actual == Decimal("1234567890")


def test_round_base_ray() -> None:
    fake_base = fake_token("RAY")
    fake_quote = fake_token("USDC")
    # From RAY/USDC on Mango spot:
    #  « 𝙻𝚘𝚝𝚂𝚒𝚣𝚎𝙲𝚘𝚗𝚟𝚎𝚛𝚝𝚎𝚛 RAY/USDC [base lot size: 100000 (6 decimals), quote lot size: 100 (6 decimals)] »
    sut = mango.LotSizeConverter(fake_base, Decimal(100000), fake_quote, Decimal(100))
    actual = sut.round_base(Decimal("1234567890.1234567890"))
    assert actual == Decimal("1234567890.1")


def test_round_base_sol() -> None:
    fake_base = fake_token("SOL", decimals=9)
    fake_quote = fake_token("USDC")
    # From SOL/USDC on Mango spot:
    #  « 𝙻𝚘𝚝𝚂𝚒𝚣𝚎𝙲𝚘𝚗𝚟𝚎𝚛𝚝𝚎𝚛 SOL/USDC [base lot size: 100000000 (9 decimals), quote lot size: 100 (6 decimals)] »
    sut = mango.LotSizeConverter(
        fake_base, Decimal(100000000), fake_quote, Decimal(100)
    )
    actual = sut.round_base(Decimal("1234567890.1234567890"))
    assert actual == Decimal("1234567890.1")


def test_round_base_srm() -> None:
    fake_base = fake_token("SRM")
    fake_quote = fake_token("USDC")
    # From SRM/USDC on Mango spot:
    #  « 𝙻𝚘𝚝𝚂𝚒𝚣𝚎𝙲𝚘𝚗𝚟𝚎𝚛𝚝𝚎𝚛 SRM/USDC [base lot size: 100000 (6 decimals), quote lot size: 100 (6 decimals)] »
    sut = mango.LotSizeConverter(fake_base, Decimal(100000), fake_quote, Decimal(100))
    actual = sut.round_base(Decimal("1234567890.1234567890"))
    assert actual == Decimal("1234567890.1")


def test_round_base_usdt() -> None:
    fake_base = fake_token("BASE")
    fake_quote = fake_token("USDC")
    # From USDT/USDC on Mango spot:
    #  « 𝙻𝚘𝚝𝚂𝚒𝚣𝚎𝙲𝚘𝚗𝚟𝚎𝚛𝚝𝚎𝚛 USDT/USDC [base lot size: 1000000 (6 decimals), quote lot size: 100 (6 decimals)] »
    sut = mango.LotSizeConverter(fake_base, Decimal(1000000), fake_quote, Decimal(100))
    actual = sut.round_base(Decimal("1234567890.1234567890"))
    assert actual == Decimal("1234567890")


def test_round_quote_btc() -> None:
    fake_base = fake_token("BTC")
    fake_quote = fake_token("USDC")
    # From BTC/USDC on Mango spot:
    #  « 𝙻𝚘𝚝𝚂𝚒𝚣𝚎𝙲𝚘𝚗𝚟𝚎𝚛𝚝𝚎𝚛 BTC/USDC [base lot size: 100 (6 decimals), quote lot size: 10 (6 decimals)] »
    sut = mango.LotSizeConverter(fake_base, Decimal(100), fake_quote, Decimal(10))
    actual = sut.round_quote(Decimal("1234567890.1234567890"))
    assert actual == Decimal("1234567890.1")


def test_round_quote_eth() -> None:
    fake_base = fake_token("ETH")
    fake_quote = fake_token("USDC")
    # From ETH/USDC on Mango spot:
    #  « 𝙻𝚘𝚝𝚂𝚒𝚣𝚎𝙲𝚘𝚗𝚟𝚎𝚛𝚝𝚎𝚛 ETH/USDC [base lot size: 1000 (6 decimals), quote lot size: 10 (6 decimals)] »
    sut = mango.LotSizeConverter(fake_base, Decimal(1000), fake_quote, Decimal(10))
    actual = sut.round_quote(Decimal("1234567890.1234567890"))
    assert actual == Decimal("1234567890.12")


def test_round_quote_mngo() -> None:
    fake_base = fake_token("MNGO")
    fake_quote = fake_token("USDC")
    # From MNGO/USDC on Mango spot:
    #  « 𝙻𝚘𝚝𝚂𝚒𝚣𝚎𝙲𝚘𝚗𝚟𝚎𝚛𝚝𝚎𝚛 MNGO/USDC [base lot size: 1000000 (6 decimals), quote lot size: 100 (6 decimals)] »
    sut = mango.LotSizeConverter(fake_base, Decimal(1000000), fake_quote, Decimal(100))
    actual = sut.round_quote(Decimal("1234567890.1234567890"))
    assert actual == Decimal("1234567890.1235")


def test_round_quote_ray() -> None:
    fake_base = fake_token("RAY")
    fake_quote = fake_token("USDC")
    # From RAY/USDC on Mango spot:
    #  « 𝙻𝚘𝚝𝚂𝚒𝚣𝚎𝙲𝚘𝚗𝚟𝚎𝚛𝚝𝚎𝚛 RAY/USDC [base lot size: 100000 (6 decimals), quote lot size: 100 (6 decimals)] »
    sut = mango.LotSizeConverter(fake_base, Decimal(100000), fake_quote, Decimal(100))
    actual = sut.round_quote(Decimal("1234567890.1234567890"))
    assert actual == Decimal("1234567890.123")


def test_round_quote_sol() -> None:
    fake_base = fake_token("SOL", decimals=9)
    fake_quote = fake_token("USDC")
    # From SOL/USDC on Mango spot:
    #  « 𝙻𝚘𝚝𝚂𝚒𝚣𝚎𝙲𝚘𝚗𝚟𝚎𝚛𝚝𝚎𝚛 SOL/USDC [base lot size: 100000000 (9 decimals), quote lot size: 100 (6 decimals)] »
    sut = mango.LotSizeConverter(
        fake_base, Decimal(100000000), fake_quote, Decimal(100)
    )
    actual = sut.round_quote(Decimal("1234567890.1234567890"))
    assert actual == Decimal("1234567890.123")


def test_round_quote_srm() -> None:
    fake_base = fake_token("SRM")
    fake_quote = fake_token("USDC")
    # From SRM/USDC on Mango spot:
    #  « 𝙻𝚘𝚝𝚂𝚒𝚣𝚎𝙲𝚘𝚗𝚟𝚎𝚛𝚝𝚎𝚛 SRM/USDC [base lot size: 100000 (6 decimals), quote lot size: 100 (6 decimals)] »
    sut = mango.LotSizeConverter(fake_base, Decimal(100000), fake_quote, Decimal(100))
    actual = sut.round_quote(Decimal("1234567890.1234567890"))
    assert actual == Decimal("1234567890.123")


def test_round_quote_usdt() -> None:
    fake_base = fake_token("BASE")
    fake_quote = fake_token("USDC")
    # From USDT/USDC on Mango spot:
    #  « 𝙻𝚘𝚝𝚂𝚒𝚣𝚎𝙲𝚘𝚗𝚟𝚎𝚛𝚝𝚎𝚛 USDT/USDC [base lot size: 1000000 (6 decimals), quote lot size: 100 (6 decimals)] »
    sut = mango.LotSizeConverter(fake_base, Decimal(1000000), fake_quote, Decimal(100))
    actual = sut.round_quote(Decimal("1234567890.1234567890"))
    assert actual == Decimal("1234567890.1235")


def test_round_base_ftt() -> None:
    fake_base = fake_token("FTT")
    fake_quote = fake_token("USDC")
    # From FTT/USDC on Mango perp:
    #   Base Lot Size: 100000
    #   Quote Lot Size: 100
    sut = mango.LotSizeConverter(fake_base, Decimal(100000), fake_quote, Decimal(100))
    actual = sut.round_base(Decimal("1234567890.1234567890"))
    assert actual == Decimal("1234567890.10000000")


def test_round_quote_ftt() -> None:
    fake_base = fake_token("FTT")
    fake_quote = fake_token("USDC")
    # From FTT/USDC on Mango perp:
    #   Base Lot Size: 100000
    #   Quote Lot Size: 100
    sut = mango.LotSizeConverter(fake_base, Decimal(100000), fake_quote, Decimal(100))
    actual = sut.round_quote(Decimal("1234567890.1234567890"))
    assert actual == Decimal("1234567890.12300000")
