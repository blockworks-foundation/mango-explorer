from .context import mango
from .fakes import fake_account_info, fake_seeded_public_key

from decimal import Decimal


def test_constructor():
    mint = fake_seeded_public_key("token mint")
    owner = fake_seeded_public_key("token owner")
    actual = mango.TokenAccount(fake_account_info, mango.Version.V1, mint, owner, Decimal(6))
    assert actual is not None
    assert actual.logger is not None
