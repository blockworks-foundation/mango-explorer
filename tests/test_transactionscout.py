import typing

from .context import mango
from .fakes import fake_mango_instruction, fake_seeded_public_key, fake_token

from datetime import datetime
from decimal import Decimal
from solana.publickey import PublicKey


def test_transaction_instruction_constructor() -> None:
    instruction_type: mango.InstructionType = mango.InstructionType.Deposit
    instruction_data: typing.Dict[str, str] = {"key": "test value"}
    program_id = fake_seeded_public_key("program id")
    account1 = fake_seeded_public_key("account 1")
    account2 = fake_seeded_public_key("account 2")
    account3 = fake_seeded_public_key("account 3")
    accounts = [account1, account2, account3]
    actual = mango.MangoInstruction(
        program_id, instruction_type, bytes(), instruction_data, accounts
    )
    assert actual is not None
    assert actual.instruction_type == instruction_type
    assert actual.instruction_data == instruction_data
    assert actual.accounts == accounts


def test_transaction_scout_constructor() -> None:
    timestamp: datetime = mango.utc_now()
    signatures: typing.Sequence[str] = ["Signature1", "Signature2"]
    succeeded: bool = True
    group_name: str = "BTC_ETH_USDT"
    account1: PublicKey = fake_seeded_public_key("account 1")
    account2: PublicKey = fake_seeded_public_key("account 2")
    account3: PublicKey = fake_seeded_public_key("account 3")
    accounts: typing.Sequence[PublicKey] = [account1, account2, account3]
    instructions: typing.Sequence[mango.MangoInstruction] = [fake_mango_instruction()]
    messages: typing.Sequence[str] = ["Message 1", "Message 2"]
    token = fake_token()
    token_value = mango.InstrumentValue(token, Decimal(28))
    owner = fake_seeded_public_key("owner")
    owned_token_value = mango.OwnedInstrumentValue(owner, token_value)
    pre_token_balances: typing.Sequence[mango.OwnedInstrumentValue] = [
        owned_token_value
    ]
    post_token_balances: typing.Sequence[mango.OwnedInstrumentValue] = [
        owned_token_value
    ]
    actual = mango.TransactionScout(
        timestamp,
        signatures,
        succeeded,
        group_name,
        accounts,
        instructions,
        messages,
        pre_token_balances,
        post_token_balances,
    )
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
