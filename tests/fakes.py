import datetime
import mango

from decimal import Decimal
from pyserum.market import Market as PySerumMarket
from pyserum.market.state import MarketState as PySerumMarketState
from solana.account import Account
from solana.publickey import PublicKey
from solana.rpc.types import RPCResponse
from typing import NamedTuple


class MockCompatibleClient(mango.CompatibleClient):
    def __init__(self):
        super().__init__("test", "local", "http://localhost", "processed", "base64", mango.InstructionReporter())
        self.token_accounts_by_owner = []

    def get_token_accounts_by_owner(self, *args, **kwargs) -> RPCResponse:
        return RPCResponse(result={"value": self.token_accounts_by_owner})

    def get_minimum_balance_for_rent_exemption(size, *args, **kwargs) -> RPCResponse:
        return RPCResponse(result=27)


class MockClient(mango.BetterClient):
    def __init__(self):
        super().__init__(MockCompatibleClient())


def fake_public_key() -> PublicKey:
    return PublicKey("11111111111111111111111111111112")


def fake_seeded_public_key(seed: str) -> PublicKey:
    return PublicKey.create_with_seed(PublicKey("11111111111111111111111111111112"), seed, PublicKey("11111111111111111111111111111111"))


def fake_account_info(address: PublicKey = fake_public_key(), executable: bool = False, lamports: Decimal = Decimal(0), owner: PublicKey = fake_public_key(), rent_epoch: Decimal = Decimal(0), data: bytes = bytes([0])):
    return mango.AccountInfo(address, executable, lamports, owner, rent_epoch, data)


def fake_token(symbol: str = "FAKE") -> mango.Token:
    return mango.Token(symbol, f"Fake Token ({symbol})", fake_seeded_public_key(f"fake token ({symbol})"), Decimal(6))


def fake_token_info() -> mango.TokenInfo:
    token = fake_token()
    meta_data = mango.Metadata(mango.layouts.DATA_TYPE.Group, mango.Version.V1, True)
    root_bank = mango.RootBank(fake_account_info(), mango.Version.V1, meta_data, [],
                               Decimal(5), Decimal(2), datetime.datetime.now())
    return mango.TokenInfo(token, root_bank, Decimal(7))


def fake_context() -> mango.Context:
    context = mango.Context(name="Mango Test",
                            cluster="test",
                            cluster_url="http://localhost",
                            skip_preflight=False,
                            program_id=fake_seeded_public_key("program ID"),
                            dex_program_id=fake_seeded_public_key("DEX program ID"),
                            group_name="TEST_GROUP",
                            group_id=fake_seeded_public_key("group ID"),
                            token_lookup=mango.NullTokenLookup(),
                            market_lookup=mango.NullMarketLookup())
    context.client = MockClient()
    return context


def fake_market() -> PySerumMarket:
    Container = NamedTuple("Container", [("own_address", PublicKey), ("vault_signer_nonce", int)])
    container = Container(own_address=fake_seeded_public_key("market address"), vault_signer_nonce=2)
    state = PySerumMarketState(container, fake_seeded_public_key("program ID"), 6, 6)
    state.base_vault = lambda: fake_seeded_public_key("base vault")
    state.quote_vault = lambda: fake_seeded_public_key("quote vault")
    state.event_queue = lambda: fake_seeded_public_key("event queue")
    state.request_queue = lambda: fake_seeded_public_key("request queue")
    state.bids = lambda: fake_seeded_public_key("bids")
    state.asks = lambda: fake_seeded_public_key("asks")
    state.base_lot_size = lambda: 1
    state.quote_lot_size = lambda: 1
    return PySerumMarket(None, state)


def fake_spot_market_stub() -> mango.SpotMarketStub:
    return mango.SpotMarketStub(fake_seeded_public_key("program ID"), fake_seeded_public_key("spot market"), fake_token("BASE"), fake_token("QUOTE"), fake_seeded_public_key("group address"))


def fake_token_account() -> mango.TokenAccount:
    token_account_info = fake_account_info()
    token = fake_token()
    token_value = mango.TokenValue(token, Decimal("100"))
    return mango.TokenAccount(token_account_info, mango.Version.V1, fake_seeded_public_key("owner"), token_value)


def fake_token_value(value: Decimal = Decimal(100)) -> mango.TokenValue:
    return mango.TokenValue(fake_token(), value)


def fake_wallet() -> mango.Wallet:
    wallet = mango.Wallet([1] * 64)
    wallet.account = Account()
    return wallet
