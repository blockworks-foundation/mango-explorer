from .context import mango
from .fakes import fake_index, fake_seeded_public_key, fake_token

from decimal import Decimal


def test_constructor():
    base = mango.BasketToken(fake_token(), fake_seeded_public_key("base vault"), fake_index())
    quote = mango.BasketToken(fake_token(), fake_seeded_public_key("quote vault"), fake_index())
    spot_market = mango.SpotMarket(fake_seeded_public_key("spot market"), base, quote)
    actual = mango.MarketMetadata("FAKE/MKT", fake_seeded_public_key("market metadata"),
                                  base, quote, spot_market, fake_seeded_public_key("oracle"), Decimal(7))
    assert actual is not None
    assert actual.logger is not None
