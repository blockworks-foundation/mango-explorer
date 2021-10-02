import construct
import datetime
import mango
import mango.marketmaking
import typing

from decimal import Decimal
from pyserum.market import Market as PySerumMarket
from pyserum.market.state import MarketState as PySerumMarketState
from solana.account import Account
from solana.publickey import PublicKey
from solana.rpc.types import RPCResponse


class MockCompatibleClient(mango.CompatibleClient):
    def __init__(self):
        super().__init__("test", "local", "http://localhost", "processed", "processed",
                         False, "base64", datetime.timedelta(seconds=5), mango.InstructionReporter())
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


def fake_token(symbol: str = "FAKE", decimals: int = 6) -> mango.Token:
    return mango.Token(symbol, f"Fake Token ({symbol})", fake_seeded_public_key(f"fake token ({symbol})"), Decimal(decimals))


def fake_token_info() -> mango.TokenInfo:
    token = fake_token()
    meta_data = mango.Metadata(mango.layouts.DATA_TYPE.Group, mango.Version.V1, True)
    root_bank = mango.RootBank(fake_account_info(), mango.Version.V1, meta_data, [],
                               Decimal(5), Decimal(2), datetime.datetime.now())
    return mango.TokenInfo(token, root_bank, Decimal(7))


def fake_context() -> mango.Context:
    context = mango.Context(name="Mango Test",
                            cluster_name="test",
                            cluster_url="http://localhost",
                            skip_preflight=False,
                            commitment="processed",
                            blockhash_commitment="processed",
                            encoding="base64",
                            blockhash_cache_duration=datetime.timedelta(seconds=5),
                            mango_program_address=fake_seeded_public_key("Mango program address"),
                            serum_program_address=fake_seeded_public_key("Serum program address"),
                            group_name="TEST_GROUP",
                            group_address=fake_seeded_public_key("group ID"),
                            gma_chunk_size=Decimal(20),
                            gma_chunk_pause=Decimal(25),
                            token_lookup=mango.NullTokenLookup(),
                            market_lookup=mango.NullMarketLookup())
    context.client = MockClient()
    return context


def fake_market() -> PySerumMarket:
    # Container = NamedTuple("Container", [("own_address", PublicKey), ("vault_signer_nonce", int)])
    container = construct.Container({"own_address": fake_seeded_public_key("market address"), "vault_signer_nonce": 2})
    # container: Container[typing.Any] = Container(
    #     own_address=fake_seeded_public_key("market address"), vault_signer_nonce=2)
    state = PySerumMarketState(container, fake_seeded_public_key("program ID"), 6, 6)
    state.base_vault = lambda: fake_seeded_public_key("base vault")  # type: ignore[assignment]
    state.quote_vault = lambda: fake_seeded_public_key("quote vault")  # type: ignore[assignment]
    state.event_queue = lambda: fake_seeded_public_key("event queue")  # type: ignore[assignment]
    state.request_queue = lambda: fake_seeded_public_key("request queue")  # type: ignore[assignment]
    state.bids = lambda: fake_seeded_public_key("bids")  # type: ignore[assignment]
    state.asks = lambda: fake_seeded_public_key("asks")  # type: ignore[assignment]
    state.base_lot_size = lambda: 1  # type: ignore[assignment]
    state.quote_lot_size = lambda: 1  # type: ignore[assignment]
    return PySerumMarket(MockCompatibleClient(), state)


def fake_spot_market_stub() -> mango.SpotMarketStub:
    return mango.SpotMarketStub(fake_seeded_public_key("program ID"), fake_seeded_public_key("spot market"), fake_token("BASE"), fake_token("QUOTE"), fake_seeded_public_key("group address"))


def fake_loaded_market(base_lot_size: Decimal = Decimal(1), quote_lot_size: Decimal = Decimal(1)) -> mango.LoadedMarket:
    base = fake_token("BASE")
    quote = fake_token("QUOTE")
    return mango.LoadedMarket(fake_seeded_public_key("program ID"), fake_seeded_public_key("perp market"), mango.InventorySource.ACCOUNT, base, quote, mango.LotSizeConverter(base, base_lot_size, quote, quote_lot_size))


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


def fake_order(price: Decimal = Decimal(1), quantity: Decimal = Decimal(1), side: mango.Side = mango.Side.BUY, order_type: mango.OrderType = mango.OrderType.LIMIT) -> mango.Order:
    return mango.Order.from_basic_info(side=side, price=price, quantity=quantity, order_type=order_type)


def fake_group():
    return None


def fake_account():
    return None


def fake_price(market: mango.Market = fake_loaded_market(), price: Decimal = Decimal(100)):
    return mango.Price(mango.OracleSource("test", "test", mango.SupportedOracleFeature.MID_PRICE, market), datetime.datetime.now(), market, price, price, price, Decimal(0))


def fake_placed_orders_container():
    return None


def fake_inventory():
    return None


def fake_bids():
    return None


def fake_asks():
    return None


def fake_model_state(order_owner: typing.Optional[PublicKey] = None,
                     market: typing.Optional[mango.Market] = None,
                     group: typing.Optional[mango.Group] = None,
                     account: typing.Optional[mango.Account] = None,
                     price: typing.Optional[mango.Price] = None,
                     placed_orders_container: typing.Optional[mango.PlacedOrdersContainer] = None,
                     inventory: typing.Optional[mango.Inventory] = None,
                     bids: typing.Optional[typing.Sequence[mango.Order]] = None,
                     asks: typing.Optional[typing.Sequence[mango.Order]] = None) -> mango.ModelState:
    order_owner = order_owner or fake_seeded_public_key("order owner")
    market = market or fake_loaded_market()
    group = group or fake_group()
    account = account or fake_account()
    price = price or fake_price()
    placed_orders_container = placed_orders_container or fake_placed_orders_container()
    inventory = inventory or fake_inventory()
    bids = bids or fake_bids()
    asks = asks or fake_asks()
    group_watcher: mango.ManualUpdateWatcher[mango.Group] = mango.ManualUpdateWatcher(group)
    account_watcher: mango.ManualUpdateWatcher[mango.Account] = mango.ManualUpdateWatcher(account)
    price_watcher: mango.ManualUpdateWatcher[mango.Price] = mango.ManualUpdateWatcher(price)
    placed_orders_container_watcher: mango.ManualUpdateWatcher[
        mango.PlacedOrdersContainer] = mango.ManualUpdateWatcher(placed_orders_container)
    inventory_watcher: mango.ManualUpdateWatcher[mango.Inventory] = mango.ManualUpdateWatcher(inventory)
    bids_watcher: mango.ManualUpdateWatcher[typing.Sequence[mango.Order]] = mango.ManualUpdateWatcher(bids)
    asks_watcher: mango.ManualUpdateWatcher[typing.Sequence[mango.Order]] = mango.ManualUpdateWatcher(asks)

    return mango.ModelState(order_owner, market, group_watcher,
                            account_watcher, price_watcher, placed_orders_container_watcher,
                            inventory_watcher, bids_watcher, asks_watcher)
