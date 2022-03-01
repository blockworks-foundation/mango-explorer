from .context import mango
from .fakes import fake_account_info, fake_seeded_public_key

from decimal import Decimal


def test_constructor() -> None:
    account_info = fake_account_info()
    program_address = fake_seeded_public_key("program_address")
    market = fake_seeded_public_key("market")
    owner = fake_seeded_public_key("owner")
    base = mango.Token(
        "FAKEBASE",
        "Fake Base Token",
        Decimal(6),
        fake_seeded_public_key("fake base token"),
    )
    quote = mango.Token(
        "FAKEQUOTE",
        "Fake Quote Token",
        Decimal(6),
        fake_seeded_public_key("fake quote token"),
    )

    flags = mango.AccountFlags(
        mango.Version.V1, True, False, True, False, False, False, False, False
    )
    actual = mango.OpenOrders(
        account_info,
        mango.Version.V1,
        program_address,
        flags,
        market,
        owner,
        base,
        quote,
        Decimal(0),
        Decimal(0),
        Decimal(0),
        Decimal(0),
        [],
        Decimal(0),
    )
    assert actual is not None
