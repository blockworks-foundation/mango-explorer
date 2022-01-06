import construct
import datetime
import mango
import mango.marketmaking
import typing

from decimal import Decimal
from mango.lotsizeconverter import NullLotSizeConverter
from pyserum.market.market import Market as PySerumMarket
from pyserum.market.state import MarketState as PySerumMarketState
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.rpc.commitment import Commitment
from solana.rpc.types import RPCResponse


class MockCompatibleClient(Client):
    def __init__(self) -> None:
        super().__init__("http://localhost", Commitment("processed"))
        self.token_accounts_by_owner: typing.Sequence[typing.Any] = []

    def get_token_accounts_by_owner(self, *args: typing.Any, **kwargs: typing.Any) -> RPCResponse:
        return RPCResponse(result={"value": self.token_accounts_by_owner})

    def get_minimum_balance_for_rent_exemption(size, *args: typing.Any, **kwargs: typing.Any) -> RPCResponse:
        return RPCResponse(result=27)


class MockClient(mango.BetterClient):
    def __init__(self) -> None:
        rpc = mango.RPCCaller("fake", "http://localhost", "ws://localhost", [], mango.SlotHolder(), mango.InstructionReporter())
        compound = mango.CompoundRPCCaller("fake", [rpc])
        super().__init__(MockCompatibleClient(), "test", "local", Commitment("processed"),
                         False, "base64", 0, compound)


def fake_public_key() -> PublicKey:
    return PublicKey("11111111111111111111111111111112")


def fake_seeded_public_key(seed: str) -> PublicKey:
    return PublicKey.create_with_seed(PublicKey("11111111111111111111111111111112"), seed, PublicKey("11111111111111111111111111111111"))


def fake_context() -> mango.Context:
    context = mango.Context(name="Mango Test",
                            cluster_name="test",
                            cluster_urls=[
                                mango.ClusterUrlData(rpc="http://localhost"),
                                mango.ClusterUrlData(rpc="http://localhost")
                            ],
                            skip_preflight=False,
                            commitment="processed",
                            encoding="base64",
                            blockhash_cache_duration=0,
                            stale_data_pauses_before_retry=[],
                            mango_program_address=fake_seeded_public_key("Mango program address"),
                            serum_program_address=fake_seeded_public_key("Serum program address"),
                            group_name="TEST_GROUP",
                            group_address=fake_seeded_public_key("group ID"),
                            gma_chunk_size=Decimal(20),
                            gma_chunk_pause=Decimal(25),
                            instrument_lookup=mango.IdsJsonTokenLookup("devnet", "devnet.2"),
                            market_lookup=mango.NullMarketLookup())
    context.client = MockClient()
    return context


def fake_account_info(address: PublicKey = fake_public_key(), executable: bool = False, lamports: Decimal = Decimal(0), owner: PublicKey = fake_public_key(), rent_epoch: Decimal = Decimal(0), data: bytes = bytes([0])) -> mango.AccountInfo:
    return mango.AccountInfo(address, executable, lamports, owner, rent_epoch, data)


def fake_instrument(symbol: str = "FAKE", decimals: int = 6) -> mango.Instrument:
    return mango.Instrument(symbol, f"Fake Instrument ({symbol})", Decimal(decimals))


def fake_token(symbol: str = "FAKE", decimals: int = 6) -> mango.Token:
    return mango.Token(symbol, f"Fake Token ({symbol})", Decimal(decimals), fake_seeded_public_key(f"fake token ({symbol})"))


def fake_perp_account() -> mango.PerpAccount:
    return mango.PerpAccount(Decimal(0), Decimal(0), Decimal(0), Decimal(0), Decimal(0),
                             Decimal(0), Decimal(0), Decimal(0), fake_instrument_value(), mango.PerpOpenOrders([]),
                             mango.NullLotSizeConverter(), fake_instrument_value(), Decimal(0))


def fake_token_bank(symbol: str = "FAKE") -> mango.TokenBank:
    return mango.TokenBank(fake_token(symbol), fake_seeded_public_key("root bank"))


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
    token_value = mango.InstrumentValue(token, Decimal("100"))
    return mango.TokenAccount(token_account_info, mango.Version.V1, fake_seeded_public_key("owner"), token_value)


def fake_instrument_value(value: Decimal = Decimal(100)) -> mango.InstrumentValue:
    return mango.InstrumentValue(fake_token(), value)


def fake_wallet() -> mango.Wallet:
    wallet = mango.Wallet(bytes([1] * 64))
    wallet.keypair = Keypair()
    return wallet


def fake_order(price: Decimal = Decimal(1), quantity: Decimal = Decimal(1), side: mango.Side = mango.Side.BUY, order_type: mango.OrderType = mango.OrderType.LIMIT) -> mango.Order:
    return mango.Order.from_basic_info(side=side, price=price, quantity=quantity, order_type=order_type)


# serum ID structure - 16-byte 'int': low 8 bytes is a sequence number, high 8 bytes is price
def fake_order_id(index: int, price: int) -> int:
    # price needs to be max of 64bit/8bytes, considering signed int is not permitted
    if index > (2 ** 64) - 1 or price > (2 ** 64) - 1:
        raise ValueError(f"Provided index '{index}' or price '{price}' is bigger than 8 bytes int")
    index_bytes = index.to_bytes(8, byteorder='big', signed=False)
    price_bytes = price.to_bytes(8, byteorder='big', signed=False)
    return int.from_bytes((price_bytes + index_bytes), byteorder='big', signed=False)


def fake_price(market: mango.Market = fake_loaded_market(), price: Decimal = Decimal(100), bid: Decimal = Decimal(99), ask: Decimal = Decimal(101)) -> mango.Price:
    return mango.Price(mango.OracleSource("test", "test", mango.SupportedOracleFeature.TOP_BID_AND_OFFER, market), datetime.datetime.now(), market, bid, price, ask, Decimal(0))


def fake_placed_orders_container() -> mango.PlacedOrdersContainer:
    return mango.PerpOpenOrders([])


def fake_inventory(incentives: Decimal = Decimal(1), available: Decimal = Decimal(100), base: Decimal = Decimal(10), quote: Decimal = Decimal(10)) -> mango.Inventory:
    return mango.Inventory(mango.InventorySource.SPL_TOKENS, fake_instrument_value(incentives), fake_instrument_value(available), fake_instrument_value(base), fake_instrument_value(quote))


def fake_bids() -> typing.Sequence[mango.Order]:
    return []


def fake_asks() -> typing.Sequence[mango.Order]:
    return []


def fake_account_slot() -> mango.AccountSlot:
    return mango.AccountSlot(1, fake_instrument(), fake_token_bank(), fake_token_bank(), Decimal(1),
                             fake_instrument_value(), Decimal(0), fake_instrument_value(),
                             fake_seeded_public_key("open_orders"), None)


def fake_account() -> mango.Account:
    meta_data = mango.Metadata(mango.layouts.DATA_TYPE.Account, mango.Version.V1, True)
    quote = fake_account_slot()
    return mango.Account(fake_account_info(), mango.Version.V1, meta_data, "GROUPNAME",
                         fake_seeded_public_key("group"), fake_seeded_public_key("owner"), "INFO",
                         quote, [], [], [], Decimal(1), False, False, fake_seeded_public_key("advanced_orders"),
                         False, fake_seeded_public_key("delegate"))


def fake_root_bank() -> mango.RootBank:
    meta_data = mango.Metadata(mango.layouts.DATA_TYPE.RootBank, mango.Version.V1, True)
    return mango.RootBank(fake_account_info(), mango.Version.V1, meta_data, Decimal(0), Decimal(0),
                          Decimal(0), [], Decimal(0), Decimal(0), datetime.datetime.now())


def fake_cache() -> mango.Cache:
    meta_data = mango.Metadata(mango.layouts.DATA_TYPE.RootBank, mango.Version.V1, True)
    return mango.Cache(fake_account_info(), mango.Version.V1, meta_data, [], [], [])


def fake_root_bank_cache() -> mango.RootBankCache:
    return mango.RootBankCache(Decimal(1), Decimal(2), datetime.datetime.now())


def fake_group() -> mango.Group:
    account_info = fake_account_info()
    name = "FAKE_GROUP"
    meta_data = mango.Metadata(mango.layouts.DATA_TYPE.Group, mango.Version.V1, True)
    instrument_lookup = fake_context().instrument_lookup
    usdc = mango.Token.ensure(instrument_lookup.find_by_symbol_or_raise("usdc"))
    quote_info = mango.TokenBank(usdc, fake_seeded_public_key("root bank"))
    signer_nonce = Decimal(1)
    signer_key = fake_seeded_public_key("signer key")
    admin_key = fake_seeded_public_key("admin key")
    serum_program_address = fake_seeded_public_key("DEX program ID")
    cache_key = fake_seeded_public_key("cache key")
    valid_interval = Decimal(7)
    insurance_vault = fake_seeded_public_key("insurance vault")
    srm_vault = fake_seeded_public_key("srm vault")
    msrm_vault = fake_seeded_public_key("msrm vault")
    fees_vault = fake_seeded_public_key("fees vault")
    max_mango_accounts = Decimal(1000000)
    num_mango_accounts = Decimal(1)

    return mango.Group(account_info, mango.Version.V1, name, meta_data, quote_info, [], [],
                       signer_nonce, signer_key, admin_key, serum_program_address, cache_key,
                       valid_interval, insurance_vault, srm_vault, msrm_vault, fees_vault,
                       max_mango_accounts, num_mango_accounts)


def fake_prices(prices: typing.Sequence[str]) -> typing.Sequence[mango.InstrumentValue]:
    instrument_lookup = fake_context().instrument_lookup
    ETH = mango.Token.ensure(instrument_lookup.find_by_symbol_or_raise("ETH"))
    BTC = mango.Token.ensure(instrument_lookup.find_by_symbol_or_raise("BTC"))
    SOL = mango.Token.ensure(instrument_lookup.find_by_symbol_or_raise("SOL"))
    SRM = mango.Token.ensure(instrument_lookup.find_by_symbol_or_raise("SRM"))
    USDC = mango.Token.ensure(instrument_lookup.find_by_symbol_or_raise("USDC"))
    eth, btc, sol, srm, usdc = prices

    return [
        mango.InstrumentValue(ETH, Decimal(eth)),
        mango.InstrumentValue(BTC, Decimal(btc)),
        mango.InstrumentValue(SOL, Decimal(sol)),
        mango.InstrumentValue(SRM, Decimal(srm)),
        mango.InstrumentValue(USDC, Decimal(usdc)),
    ]


def fake_open_orders(base_token_free: Decimal = Decimal(0), base_token_total: Decimal = Decimal(0),
                     quote_token_free: Decimal = Decimal(0), quote_token_total: Decimal = Decimal(0),
                     referrer_rebate_accrued: Decimal = Decimal(0)) -> mango.OpenOrders:
    account_info = fake_account_info()
    program_address = fake_seeded_public_key("program address")
    market = fake_seeded_public_key("market")
    owner = fake_seeded_public_key("owner")

    flags = mango.AccountFlags(mango.Version.V1, True, False, True, False, False, False, False, False)
    return mango.OpenOrders(account_info, mango.Version.V1, program_address, flags, market,
                            owner, base_token_free, base_token_total, quote_token_free,
                            quote_token_total, [], referrer_rebate_accrued)


def fake_model_state(order_owner: typing.Optional[PublicKey] = None,
                     market: typing.Optional[mango.Market] = None,
                     group: typing.Optional[mango.Group] = None,
                     account: typing.Optional[mango.Account] = None,
                     price: typing.Optional[mango.Price] = None,
                     placed_orders_container: typing.Optional[mango.PlacedOrdersContainer] = None,
                     inventory: typing.Optional[mango.Inventory] = None,
                     orderbook: typing.Optional[mango.OrderBook] = None,
                     event_queue: typing.Optional[mango.EventQueue] = None) -> mango.ModelState:
    order_owner = order_owner or fake_seeded_public_key("order owner")
    market = market or fake_loaded_market()
    group = group or fake_group()
    account = account or fake_account()
    price = price or fake_price()
    placed_orders_container = placed_orders_container or fake_placed_orders_container()
    inventory = inventory or fake_inventory()
    orderbook = orderbook or mango.OrderBook("FAKE", NullLotSizeConverter(), fake_bids(), fake_asks())
    event_queue = event_queue or mango.NullEventQueue()
    group_watcher: mango.ManualUpdateWatcher[mango.Group] = mango.ManualUpdateWatcher(group)
    account_watcher: mango.ManualUpdateWatcher[mango.Account] = mango.ManualUpdateWatcher(account)
    price_watcher: mango.ManualUpdateWatcher[mango.Price] = mango.ManualUpdateWatcher(price)
    placed_orders_container_watcher: mango.ManualUpdateWatcher[
        mango.PlacedOrdersContainer] = mango.ManualUpdateWatcher(placed_orders_container)
    inventory_watcher: mango.ManualUpdateWatcher[mango.Inventory] = mango.ManualUpdateWatcher(inventory)
    orderbook_watcher: mango.ManualUpdateWatcher[mango.OrderBook] = mango.ManualUpdateWatcher(orderbook)
    event_queue_watcher: mango.ManualUpdateWatcher[mango.EventQueue] = mango.ManualUpdateWatcher(event_queue)

    return mango.ModelState(order_owner, market, group_watcher, account_watcher, price_watcher,
                            placed_orders_container_watcher, inventory_watcher, orderbook_watcher,
                            event_queue_watcher)


def fake_mango_instruction() -> mango.MangoInstruction:
    return mango.MangoInstruction(mango.InstructionType.PlacePerpOrder, "", [fake_seeded_public_key("account")])
