import typing

from .context import mango
from .fakes import fake_context, fake_market, fake_seeded_public_key, fake_token

from decimal import Decimal
from pyserum.enums import OrderType, Side
from pyserum.market.market import Market
from solana.publickey import PublicKey


def test_instruction_builder_constructor():
    context = fake_context()
    succeeded = False
    try:
        mango.InstructionBuilder(context)
    except TypeError:
        # Can't instantiate the abstract base class.
        succeeded = True
    assert succeeded


def test_create_spl_account_instruction_builder_constructor():
    context: mango.Context = fake_context()
    wallet: mango.Wallet = {"fake": "Wallet"}
    new_spl_account: PublicKey = fake_seeded_public_key("new SPL account")
    actual = mango.CreateSplAccountInstructionBuilder(context, wallet, new_spl_account)
    assert actual is not None
    assert actual.logger is not None
    assert actual.context == context
    assert actual.wallet == wallet
    assert actual.address == new_spl_account


def test_initialize_spl_account_instruction_builder_constructor():
    context: mango.Context = fake_context()
    wallet: mango.Wallet = {"fake": "Wallet"}
    token: mango.Token = fake_token()
    new_spl_account: PublicKey = fake_seeded_public_key("new SPL account")
    actual = mango.InitializeSplAccountInstructionBuilder(context, wallet, token, new_spl_account)
    assert actual is not None
    assert actual.logger is not None
    assert actual.context == context
    assert actual.wallet == wallet
    assert actual.token == token
    assert actual.address == new_spl_account


def test_transfer_spl_tokens_instruction_builder_constructor():
    context: mango.Context = fake_context()
    wallet: mango.Wallet = {"fake": "Wallet"}
    token: mango.Token = fake_token()
    source: PublicKey = fake_seeded_public_key("source SPL account")
    destination: PublicKey = fake_seeded_public_key("destination SPL account")
    quantity: int = 7
    actual = mango.TransferSplTokensInstructionBuilder(context, wallet, token, source, destination, quantity)
    assert actual is not None
    assert actual.logger is not None
    assert actual.context == context
    assert actual.wallet == wallet
    assert actual.token == token
    assert actual.source == source
    assert actual.destination == destination
    assert actual.amount == int(quantity * (10 ** token.decimals))


def test_close_spl_account_instruction_builder_constructor():
    context: mango.Context = fake_context()
    wallet: mango.Wallet = {"fake": "Wallet"}
    address: PublicKey = fake_seeded_public_key("target SPL account")
    actual = mango.CloseSplAccountInstructionBuilder(context, wallet, address)
    assert actual is not None
    assert actual.logger is not None
    assert actual.context == context
    assert actual.wallet == wallet
    assert actual.address == address


def test_create_serum_open_orders_instruction_builder_constructor():
    context: mango.Context = fake_context()
    wallet: mango.Wallet = {"fake": "Wallet"}
    market: Market = {"fake": "Market"}
    open_orders_address: PublicKey = fake_seeded_public_key("open orders account")
    actual = mango.CreateSerumOpenOrdersInstructionBuilder(context, wallet, market, open_orders_address)
    assert actual is not None
    assert actual.logger is not None
    assert actual.context == context
    assert actual.wallet == wallet
    assert actual.market == market
    assert actual.open_orders_address == open_orders_address


def test_new_order_v3_instruction_builder_constructor():
    context: mango.Context = fake_context()
    wallet: mango.Wallet = {"fake": "Wallet"}
    market: Market = {"fake": "Market"}
    source: PublicKey = fake_seeded_public_key("source")
    open_orders_address: PublicKey = fake_seeded_public_key("open orders account")
    order_type: OrderType = OrderType.IOC
    side: Side = Side.BUY
    price: Decimal = Decimal(72)
    quantity: Decimal = Decimal("0.05")
    client_id: int = 53
    fee_discount_address: PublicKey = fake_seeded_public_key("fee discount address")
    actual = mango.NewOrderV3InstructionBuilder(
        context, wallet, market, source, open_orders_address, order_type, side, price, quantity, client_id, fee_discount_address)
    assert actual is not None
    assert actual.logger is not None
    assert actual.context == context
    assert actual.wallet == wallet
    assert actual.market == market
    assert actual.source == source
    assert actual.open_orders_address == open_orders_address
    assert actual.order_type == order_type
    assert actual.side == side
    assert actual.price == price
    assert actual.quantity == quantity
    assert actual.client_id == client_id
    assert actual.fee_discount_address == fee_discount_address


def test_consume_events_instruction_builder_constructor():
    context: mango.Context = fake_context()
    wallet: mango.Wallet = {"fake": "Wallet"}
    market: Market = {"fake": "Market"}
    open_orders_addresses: typing.Sequence[PublicKey] = [fake_seeded_public_key("open orders account")]
    limit: int = 64
    actual = mango.ConsumeEventsInstructionBuilder(context, wallet, market, open_orders_addresses, limit)
    assert actual is not None
    assert actual.logger is not None
    assert actual.context == context
    assert actual.wallet == wallet
    assert actual.market == market
    assert actual.open_orders_addresses == open_orders_addresses
    assert actual.limit == limit


def test_settle_instruction_builder_constructor():
    market = fake_market()
    context: mango.Context = fake_context()
    wallet: mango.Wallet = {"fake": "Wallet"}
    open_orders_address: PublicKey = fake_seeded_public_key("open orders account")
    base_token_account_address: PublicKey = fake_seeded_public_key("base token account")
    quote_token_account_address: PublicKey = fake_seeded_public_key("quote token account")
    actual = mango.SettleInstructionBuilder(
        context, wallet, market, open_orders_address, base_token_account_address, quote_token_account_address)
    assert actual is not None
    assert actual.logger is not None
    assert actual.context == context
    assert actual.wallet == wallet
    assert actual.market == market
    assert actual.open_orders_address == open_orders_address
    assert actual.base_token_account_address == base_token_account_address
    assert actual.quote_token_account_address == quote_token_account_address
