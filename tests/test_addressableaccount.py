import typing

from .context import mango
from .fakes import fake_account_info


def test_constructor() -> None:
    class __derived(mango.AddressableAccount):
        def subscribe(
            self,
            context: mango.Context,
            websocketmanager: mango.WebSocketSubscriptionManager,
            callback: typing.Callable[[mango.AddressableAccount], None],
        ) -> mango.Disposable:
            raise NotImplementedError(
                "AddressableAccount.subscribe is not implemented on this test class."
            )

    account_info = fake_account_info()
    actual = __derived(account_info)
    assert actual is not None
    assert actual.address == account_info.address
