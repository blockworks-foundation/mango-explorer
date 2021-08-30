from .context import mango
from .fakes import fake_seeded_public_key

from decimal import Decimal


def test_spot_market_stub_constructor():
    program_address = fake_seeded_public_key("program address")
    address = fake_seeded_public_key("spot market address")
    base = mango.Token("BASE", "Base Token", fake_seeded_public_key("base token"), Decimal(7))
    quote = mango.Token("QUOTE", "Quote Token", fake_seeded_public_key("quote token"), Decimal(9))
    group_address = fake_seeded_public_key("group address")
    actual = mango.SpotMarketStub(program_address, address, base, quote, group_address)
    assert actual is not None
    assert actual.logger is not None
    assert actual.base == base
    assert actual.quote == quote
    assert actual.address == address
    assert actual.program_address == program_address
    assert actual.group_address == group_address
