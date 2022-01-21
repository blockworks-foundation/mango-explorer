import pytest
import typing

from .context import mango

from solana.rpc.types import RPCMethod, RPCResponse


__FAKE_RPC_METHOD = RPCMethod("fake")


class FakeRPCCaller(mango.RPCCaller):
    def __init__(self) -> None:
        super().__init__("Fake", "https://localhost", "wss://localhost", [0.1, 0.2], mango.SlotHolder(), mango.InstructionReporter())
        self.called = False

    def make_request(self, method: RPCMethod, *params: typing.Any) -> RPCResponse:
        self.called = True
        return {
            "jsonrpc": "2.0",
            "id": 0,
            "result": {}
        }


class RaisingRPCCaller(mango.RPCCaller):
    def __init__(self) -> None:
        super().__init__("Fake", "https://localhost", "wss://localhost", [0.1, 0.2], mango.SlotHolder(), mango.InstructionReporter())
        self.called = False

    def make_request(self, method: RPCMethod, *params: typing.Any) -> RPCResponse:
        self.called = True
        raise mango.TooManyRequestsRateLimitException("Fake", "fake-name", "https://fake")


def test_constructor_sets_correct_values() -> None:
    provider = FakeRPCCaller()
    actual = mango.CompoundRPCCaller("fake", [provider])
    assert actual is not None
    assert len(actual.all_providers) == 1
    assert actual.current == provider
    assert actual.all_providers[0] == provider


def test_constructor_sets_correct_values_with_three_providers() -> None:
    provider1 = FakeRPCCaller()
    provider2 = FakeRPCCaller()
    provider3 = FakeRPCCaller()
    actual = mango.CompoundRPCCaller("fake", [provider1, provider2, provider3])
    assert actual is not None
    assert len(actual.all_providers) == 3
    assert actual.current == provider1
    assert actual.all_providers[0] == provider1
    assert actual.all_providers[1] == provider2
    assert actual.all_providers[2] == provider3

    # Paranoid check to make sure we don't have equality issues
    assert actual.all_providers[0] != provider2
    assert actual.all_providers[0] != provider3


def test_switching_with_one_provider() -> None:
    provider = FakeRPCCaller()
    actual = mango.CompoundRPCCaller("fake", [provider])

    assert actual.current == provider
    actual.shift_to_next_provider()
    assert actual.current == provider


def test_switching_with_three_providers() -> None:
    provider1 = FakeRPCCaller()
    provider2 = FakeRPCCaller()
    provider3 = FakeRPCCaller()
    actual = mango.CompoundRPCCaller("fake", [provider1, provider2, provider3])

    assert actual.current == provider1
    actual.shift_to_next_provider()
    assert actual.current == provider2


def test_switching_with_three_providers_circular() -> None:
    provider1 = FakeRPCCaller()
    provider2 = FakeRPCCaller()
    provider3 = FakeRPCCaller()
    actual = mango.CompoundRPCCaller("fake", [provider1, provider2, provider3])

    assert actual.current == provider1

    actual.shift_to_next_provider()
    assert actual.current == provider2

    actual.shift_to_next_provider()
    assert actual.current == provider3

    actual.shift_to_next_provider()
    assert actual.current == provider1


def test_successful_calling_does_not_call_second_provider() -> None:
    provider1 = FakeRPCCaller()
    provider2 = FakeRPCCaller()
    provider3 = FakeRPCCaller()
    actual = mango.CompoundRPCCaller("fake", [provider1, provider2, provider3])

    assert not provider1.called
    assert not provider2.called
    assert not provider3.called

    actual.make_request(__FAKE_RPC_METHOD, "fake")

    assert provider1.called
    assert not provider2.called
    assert not provider3.called


def test_failed_calling_calls_second_provider() -> None:
    provider1 = RaisingRPCCaller()
    provider2 = FakeRPCCaller()
    provider3 = FakeRPCCaller()
    actual = mango.CompoundRPCCaller("fake", [provider1, provider2, provider3])

    assert not provider1.called
    assert not provider2.called
    assert not provider3.called

    actual.make_request(__FAKE_RPC_METHOD, "fake")

    assert provider1.called
    assert provider2.called
    assert not provider3.called


def test_failed_calling_updates_current_to_second_provider() -> None:
    provider1 = RaisingRPCCaller()
    provider2 = FakeRPCCaller()
    provider3 = FakeRPCCaller()
    actual = mango.CompoundRPCCaller("fake", [provider1, provider2, provider3])

    assert actual.current == provider1

    actual.make_request(__FAKE_RPC_METHOD, "fake")

    assert actual.current == provider2


def test_all_failing_raises_exception() -> None:
    provider1 = RaisingRPCCaller()
    provider2 = RaisingRPCCaller()
    provider3 = RaisingRPCCaller()
    actual = mango.CompoundRPCCaller("fake", [provider1, provider2, provider3])

    assert actual.current == provider1

    with pytest.raises(mango.CompoundException):
        actual.make_request(__FAKE_RPC_METHOD, "fake")

    assert actual.current == provider1
