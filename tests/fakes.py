import datetime

from decimal import Decimal
from typing import NamedTuple
from pyserum import market
from pyserum.market.state import MarketState
from solana.account import Account
from solana.publickey import PublicKey
from solana.rpc.types import RPCResponse

import mango


class MockClient(mango.Client):
    def __init__(self):
        super().__init__("local", "http://localhost", "processed", False)
        self.token_accounts_by_owner = []

    def get_token_accounts_by_owner(self, *args, **kwargs) -> RPCResponse:
        return RPCResponse(result={"value": self.token_accounts_by_owner})


def fake_public_key() -> PublicKey:
    return PublicKey("11111111111111111111111111111112")


def fake_seeded_public_key(seed: str) -> PublicKey:
    return PublicKey.create_with_seed(PublicKey("11111111111111111111111111111112"), seed, PublicKey("11111111111111111111111111111111"))


def fake_account_info(address: PublicKey = fake_public_key(), executable: bool = False, lamports: Decimal = Decimal(0), owner: PublicKey = fake_public_key(), rent_epoch: Decimal = Decimal(0), data: bytes = bytes([0])):
    return mango.AccountInfo(address, executable, lamports, owner, rent_epoch, data)


def fake_token() -> mango.Token:
    return mango.Token("FAKE", "Fake Token", fake_seeded_public_key("fake token"), Decimal(6))


def fake_context() -> mango.Context:
    context = mango.Context(cluster="test",
                            cluster_url="http://localhost",
                            program_id=fake_seeded_public_key("program ID"),
                            dex_program_id=fake_seeded_public_key("DEX program ID"),
                            group_name="TEST_GROUP",
                            group_id=fake_seeded_public_key("group ID"))
    context.client = MockClient()
    return context


def fake_index() -> mango.Index:
    token = fake_token()
    borrow = mango.TokenValue(token, Decimal(0))
    deposit = mango.TokenValue(token, Decimal(0))
    return mango.Index(mango.Version.V1, token, datetime.datetime.now(), borrow, deposit)


def fake_market() -> market.Market:
    Container = NamedTuple("Container", [("own_address", PublicKey), ("vault_signer_nonce", int)])
    container = Container(own_address=fake_seeded_public_key("market address"), vault_signer_nonce=2)
    state = MarketState(container, fake_seeded_public_key("program ID"), 6, 6)
    return market.Market(None, state)


def fake_token_account() -> mango.TokenAccount:
    token_account_info = fake_account_info()
    token = fake_token()
    token_value = mango.TokenValue(token, Decimal("100"))
    return mango.TokenAccount(token_account_info, mango.Version.V1, fake_seeded_public_key("owner"), token_value)


def fake_wallet() -> mango.Wallet:
    wallet = mango.Wallet([1] * 64)
    wallet.account = Account()
    return wallet
