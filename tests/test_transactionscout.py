from .context import mango
from .fakes import fake_seeded_public_key, fake_token

from datetime import datetime
from decimal import Decimal
from solana.publickey import PublicKey

import typing


def test_transaction_instruction_constructor():
    instruction_type: mango.InstructionType = mango.InstructionType.PartialLiquidate
    instruction_data: typing.Dict[str, str] = {"key": "test value"}
    account1 = fake_seeded_public_key("account 1")
    account2 = fake_seeded_public_key("account 2")
    account3 = fake_seeded_public_key("account 3")
    accounts = [account1, account2, account3]
    actual = mango.MangoInstruction(instruction_type, instruction_data, accounts)
    assert actual is not None
    assert actual.instruction_type == instruction_type
    assert actual.instruction_data == instruction_data
    assert actual.accounts == accounts


def test_transaction_scout_constructor():
    timestamp: datetime = datetime.now()
    signatures: typing.List[str] = ["Signature1", "Signature2"]
    succeeded: bool = True
    group_name: str = "BTC_ETH_USDT"
    account1: PublicKey = fake_seeded_public_key("account 1")
    account2: PublicKey = fake_seeded_public_key("account 2")
    account3: PublicKey = fake_seeded_public_key("account 3")
    accounts: typing.List[PublicKey] = [account1, account2, account3]
    instructions: typing.List[str] = ["Instruction"]
    messages: typing.List[str] = ["Message 1", "Message 2"]
    token = fake_token()
    token_value = mango.TokenValue(token, Decimal(28))
    owner = fake_seeded_public_key("owner")
    owned_token_value = mango.OwnedTokenValue(owner, token_value)
    pre_token_balances: typing.List[mango.OwnedTokenValue] = [owned_token_value]
    post_token_balances: typing.List[mango.OwnedTokenValue] = [owned_token_value]
    actual = mango.TransactionScout(timestamp, signatures, succeeded, group_name, accounts,
                                    instructions, messages, pre_token_balances, post_token_balances)
    assert actual is not None
    assert actual.timestamp == timestamp
    assert actual.signatures == signatures
    assert actual.succeeded == succeeded
    assert actual.group_name == group_name
    assert actual.accounts == accounts
    assert actual.instructions == instructions
    assert actual.messages == messages
    assert actual.pre_token_balances == pre_token_balances
    assert actual.post_token_balances == post_token_balances
