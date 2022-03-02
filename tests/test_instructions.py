import typing

from .context import mango
from .fakes import (
    fake_context,
    fake_market,
    fake_seeded_public_key,
    fake_token,
    fake_wallet,
)

from decimal import Decimal
from pyserum.market.market import Market as PySerumMarket
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction


def test_build_spl_create_account_instructions() -> None:
    context: mango.Context = fake_context()
    wallet: mango.Wallet = fake_wallet()
    token: mango.Token = fake_token()
    actual = mango.build_spl_create_account_instructions(context, wallet, token)
    assert actual is not None
    assert len(actual.signers) == 1
    assert len(actual.instructions) == 2
    assert actual.instructions[0] is not None
    assert isinstance(actual.instructions[0], TransactionInstruction)
    assert actual.instructions[1] is not None
    assert isinstance(actual.instructions[1], TransactionInstruction)


def test_build_spl_create_associated_account_instructions() -> None:
    context: mango.Context = fake_context()
    wallet: mango.Wallet = fake_wallet()
    token: mango.Token = fake_token()
    actual = mango.build_spl_create_associated_account_instructions(
        context, wallet, wallet.address, token
    )
    assert actual is not None
    assert len(actual.signers) == 0
    assert len(actual.instructions) == 1
    assert actual.instructions[0] is not None
    assert isinstance(actual.instructions[0], TransactionInstruction)


def test_build_spl_transfer_tokens_instructions() -> None:
    context: mango.Context = fake_context()
    wallet: mango.Wallet = fake_wallet()
    token: mango.Token = fake_token()
    source: PublicKey = fake_seeded_public_key("source SPL account")
    destination: PublicKey = fake_seeded_public_key("destination SPL account")
    quantity: Decimal = Decimal(7)
    actual = mango.build_spl_transfer_tokens_instructions(
        context, wallet, token, source, destination, quantity
    )
    assert actual is not None
    assert len(actual.signers) == 0
    assert len(actual.instructions) == 1
    assert actual.instructions[0] is not None
    assert isinstance(actual.instructions[0], TransactionInstruction)


def test_build_spl_close_account_instructions() -> None:
    context: mango.Context = fake_context()
    wallet: mango.Wallet = fake_wallet()
    address: PublicKey = fake_seeded_public_key("target SPL account")
    actual = mango.build_spl_close_account_instructions(context, wallet, address)
    assert actual is not None
    assert len(actual.signers) == 0
    assert len(actual.instructions) == 1
    assert actual.instructions[0] is not None
    assert isinstance(actual.instructions[0], TransactionInstruction)


def test_build_serum_create_openorders_instructions() -> None:
    context: mango.Context = fake_context()
    wallet: mango.Wallet = fake_wallet()
    market: PySerumMarket = fake_market()
    actual = mango.build_serum_create_openorders_instructions(context, wallet, market)
    assert actual is not None
    assert len(actual.signers) == 1
    assert len(actual.instructions) == 1
    assert actual.instructions[0] is not None
    assert isinstance(actual.instructions[0], TransactionInstruction)


def test_build_serum_place_order_instructions() -> None:
    context: mango.Context = fake_context()
    wallet: mango.Wallet = fake_wallet()
    market: PySerumMarket = fake_market()
    source: PublicKey = fake_seeded_public_key("source")
    open_orders_address: PublicKey = fake_seeded_public_key("open orders account")
    order_type: mango.OrderType = mango.OrderType.IOC
    side: mango.Side = mango.Side.BUY
    price: Decimal = Decimal(72)
    quantity: Decimal = Decimal("0.05")
    client_id: int = 53
    fee_discount_address: PublicKey = fake_seeded_public_key("fee discount address")
    actual = mango.build_serum_place_order_instructions(
        context,
        wallet,
        market,
        source,
        open_orders_address,
        order_type,
        side,
        price,
        quantity,
        client_id,
        fee_discount_address,
    )
    assert actual is not None
    assert len(actual.signers) == 0
    assert len(actual.instructions) == 1
    assert actual.instructions[0] is not None
    assert isinstance(actual.instructions[0], TransactionInstruction)


def test_build_serum_consume_events_instructions() -> None:
    context: mango.Context = fake_context()
    market_address: PublicKey = fake_seeded_public_key("market address")
    event_queue_address: PublicKey = fake_seeded_public_key("event queue address")
    open_orders_addresses: typing.Sequence[PublicKey] = [
        fake_seeded_public_key("open orders account")
    ]
    limit: int = 64
    actual = mango.build_serum_consume_events_instructions(
        context, market_address, event_queue_address, open_orders_addresses, limit
    )
    assert actual is not None
    assert len(actual.signers) == 0
    assert len(actual.instructions) == 1
    assert actual.instructions[0] is not None
    assert isinstance(actual.instructions[0], TransactionInstruction)


def test_build_serum_settle_instructions() -> None:
    market = fake_market()
    context: mango.Context = fake_context()
    wallet: mango.Wallet = fake_wallet()
    open_orders_address: PublicKey = fake_seeded_public_key("open orders account")
    base_token_account_address: PublicKey = fake_seeded_public_key("base token account")
    quote_token_account_address: PublicKey = fake_seeded_public_key(
        "quote token account"
    )
    actual = mango.build_serum_settle_instructions(
        context,
        wallet,
        market,
        open_orders_address,
        base_token_account_address,
        quote_token_account_address,
    )
    assert actual is not None
    assert len(actual.signers) == 0
    assert len(actual.instructions) == 1
    assert actual.instructions[0] is not None
    assert isinstance(actual.instructions[0], TransactionInstruction)
