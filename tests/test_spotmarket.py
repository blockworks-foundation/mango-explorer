from .context import mango

from decimal import Decimal
from solana.publickey import PublicKey


def test_spot_market_constructor():
    address = PublicKey("11111111111111111111111111111114")
    base = mango.Token("BASE", "Base Token", PublicKey("11111111111111111111111111111115"), Decimal(7))
    quote = mango.Token("QUOTE", "Quote Token", PublicKey("11111111111111111111111111111116"), Decimal(9))
    actual = mango.SpotMarket(base, quote, address)
    assert actual is not None
    assert actual.logger is not None
    assert actual.address == address
    assert actual.base == base
    assert actual.quote == quote
