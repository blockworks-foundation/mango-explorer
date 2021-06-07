from .context import mango
from .fakes import fake_account_info


def test_constructor():
    account_info = fake_account_info()
    actual = mango.AddressableAccount(account_info)
    assert actual is not None
    assert actual.logger is not None
    assert actual.address == account_info.address
