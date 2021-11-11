# # ⚠ Warning
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
# NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# [🥭 Mango Markets](https://mango.markets/) support is available at:
#   [Docs](https://docs.mango.markets/)
#   [Discord](https://discord.gg/67jySBhxrg)
#   [Twitter](https://twitter.com/mangomarkets)
#   [Github](https://github.com/blockworks-foundation)
#   [Email](mailto:hello@blockworks.foundation)

import logging
import typing

from decimal import Decimal
from pyserum.market.market import Market as PySerumMarket
from solana.publickey import PublicKey

from .account import Account
from .accountinfo import AccountInfo
from .cache import Cache
from .combinableinstructions import CombinableInstructions
from .context import Context
from .group import GroupSlot, Group
from .healthcheck import HealthCheck
from .instructions import build_create_serum_open_orders_instructions
from .instrumentvalue import InstrumentValue
from .inventory import Inventory
from .loadedmarket import LoadedMarket
from .market import Market, InventorySource
from .observables import DisposePropagator, LatestItemObserverSubscriber
from .openorders import OpenOrders
from .oracle import Price
from .oracle import OracleProvider
from .oraclefactory import create_oracle_provider
from .orders import OrderBook
from .perpmarket import PerpMarket
from .placedorder import PlacedOrdersContainer
from .serummarket import SerumMarket
from .spotmarket import SpotMarket
from .spotmarketoperations import SpotMarketInstructionBuilder, SpotMarketOperations
from .tokenaccount import TokenAccount
from .token import Instrument, Token
from .wallet import Wallet
from .watcher import Watcher, LamdaUpdateWatcher
from .websocketsubscription import WebSocketAccountSubscription, WebSocketSubscription, WebSocketSubscriptionManager


def build_group_watcher(context: Context, manager: WebSocketSubscriptionManager, health_check: HealthCheck, group: Group) -> Watcher[Group]:
    group_subscription = WebSocketAccountSubscription[Group](
        context, group.address, lambda account_info: Group.parse(account_info, group.name, context.instrument_lookup, context.market_lookup))
    manager.add(group_subscription)
    latest_group_observer = LatestItemObserverSubscriber[Group](group)
    group_subscription.publisher.subscribe(latest_group_observer)
    health_check.add("group_subscription", group_subscription.publisher)
    return latest_group_observer


def build_account_watcher(context: Context, manager: WebSocketSubscriptionManager, health_check: HealthCheck, account: Account, group_observer: Watcher[Group], cache_observer: Watcher[Cache]) -> typing.Tuple[WebSocketSubscription[Account], Watcher[Account]]:
    account_subscription = WebSocketAccountSubscription[Account](
        context, account.address, lambda account_info: Account.parse(account_info, group_observer.latest, cache_observer.latest))
    manager.add(account_subscription)
    latest_account_observer = LatestItemObserverSubscriber[Account](account)
    account_subscription.publisher.subscribe(latest_account_observer)
    health_check.add("account_subscription", account_subscription.publisher)
    return account_subscription, latest_account_observer


def build_cache_watcher(context: Context, manager: WebSocketSubscriptionManager, health_check: HealthCheck, cache: Cache, group: Group) -> Watcher[Cache]:
    cache_subscription = WebSocketAccountSubscription[Cache](
        context, group.cache, lambda account_info: Cache.parse(account_info))
    manager.add(cache_subscription)
    latest_cache_observer = LatestItemObserverSubscriber[Cache](cache)
    cache_subscription.publisher.subscribe(latest_cache_observer)
    health_check.add("cache_subscription", cache_subscription.publisher)
    return latest_cache_observer


def build_spot_open_orders_watcher(context: Context, manager: WebSocketSubscriptionManager, health_check: HealthCheck, wallet: Wallet, account: Account, group: Group, spot_market: SpotMarket) -> Watcher[OpenOrders]:
    market_index = group.slot_by_spot_market_address(spot_market.address).index
    open_orders_address = account.spot_open_orders_by_index[market_index]
    if open_orders_address is None:
        spot_market_instruction_builder: SpotMarketInstructionBuilder = SpotMarketInstructionBuilder.load(
            context, wallet, spot_market.group, account, spot_market)
        market_operations: SpotMarketOperations = SpotMarketOperations(
            context, wallet, spot_market.group, account, spot_market, spot_market_instruction_builder)
        open_orders_address = market_operations.create_openorders()
        logging.info(f"Created {spot_market.symbol} OpenOrders at: {open_orders_address}")

    spot_open_orders_subscription = WebSocketAccountSubscription[OpenOrders](
        context, open_orders_address, lambda account_info: OpenOrders.parse(account_info, spot_market.base.decimals, spot_market.quote.decimals))
    manager.add(spot_open_orders_subscription)
    initial_spot_open_orders = OpenOrders.load(
        context, open_orders_address, spot_market.base.decimals, spot_market.quote.decimals)
    latest_open_orders_observer = LatestItemObserverSubscriber[OpenOrders](
        initial_spot_open_orders)
    spot_open_orders_subscription.publisher.subscribe(latest_open_orders_observer)
    health_check.add("open_orders_subscription", spot_open_orders_subscription.publisher)
    return latest_open_orders_observer


def build_serum_open_orders_watcher(context: Context, manager: WebSocketSubscriptionManager, health_check: HealthCheck, serum_market: SerumMarket, wallet: Wallet) -> Watcher[PlacedOrdersContainer]:
    all_open_orders = OpenOrders.load_for_market_and_owner(
        context, serum_market.address, wallet.address, context.serum_program_address, serum_market.base.decimals, serum_market.quote.decimals)
    if len(all_open_orders) > 0:
        initial_serum_open_orders: OpenOrders = all_open_orders[0]
        open_orders_address = initial_serum_open_orders.address
    else:
        raw_market = PySerumMarket.load(context.client.compatible_client, serum_market.address)
        create_open_orders = build_create_serum_open_orders_instructions(
            context, wallet, raw_market)

        open_orders_address = create_open_orders.signers[0].public_key

        logging.info(f"Creating OpenOrders account for market {serum_market.symbol} at {open_orders_address}.")
        signers: CombinableInstructions = CombinableInstructions.from_wallet(wallet)
        transaction_ids = (signers + create_open_orders).execute(context)
        context.client.wait_for_confirmation(transaction_ids)
        initial_serum_open_orders = OpenOrders.load(
            context, open_orders_address, serum_market.base.decimals, serum_market.quote.decimals)

    serum_open_orders_subscription = WebSocketAccountSubscription[OpenOrders](
        context, open_orders_address, lambda account_info: OpenOrders.parse(account_info, serum_market.base.decimals, serum_market.quote.decimals))

    manager.add(serum_open_orders_subscription)

    latest_serum_open_orders_observer = LatestItemObserverSubscriber[PlacedOrdersContainer](
        initial_serum_open_orders)
    serum_open_orders_subscription.publisher.subscribe(latest_serum_open_orders_observer)
    health_check.add("open_orders_subscription", serum_open_orders_subscription.publisher)
    return latest_serum_open_orders_observer


def build_perp_open_orders_watcher(context: Context, manager: WebSocketSubscriptionManager, health_check: HealthCheck, perp_market: PerpMarket, account: Account, group: Group, account_subscription: WebSocketSubscription[Account]) -> Watcher[PlacedOrdersContainer]:
    slot: GroupSlot = group.slot_by_perp_market_address(perp_market.address)
    index: int = slot.index
    initial_perp_account = account.perp_accounts_by_index[slot.index]
    if initial_perp_account is None:
        raise Exception(f"Could not find perp account at index {slot.index} of account {account.address}.")
    initial_open_orders = initial_perp_account.open_orders
    latest_open_orders_observer = LatestItemObserverSubscriber[PlacedOrdersContainer](initial_open_orders)
    account_subscription.publisher.subscribe(
        on_next=lambda updated_account: latest_open_orders_observer.on_next(updated_account.perp_accounts_by_index[index].open_orders))  # type: ignore[call-arg]
    health_check.add("open_orders_subscription", account_subscription.publisher)
    return latest_open_orders_observer


def build_price_watcher(context: Context, manager: WebSocketSubscriptionManager, health_check: HealthCheck, disposer: DisposePropagator, provider_name: str, market: Market) -> LatestItemObserverSubscriber[Price]:
    oracle_provider: OracleProvider = create_oracle_provider(context, provider_name)
    oracle = oracle_provider.oracle_for_market(context, market)
    if oracle is None:
        raise Exception(f"Could not find oracle for market {market.symbol} from provider {provider_name}.")

    initial_price = oracle.fetch_price(context)
    price_feed = oracle.to_streaming_observable(context)
    latest_price_observer = LatestItemObserverSubscriber(initial_price)
    price_disposable = price_feed.subscribe(latest_price_observer)
    disposer.add_disposable(price_disposable)
    health_check.add("price_subscription", price_feed)
    return latest_price_observer


def build_serum_inventory_watcher(context: Context, manager: WebSocketSubscriptionManager, health_check: HealthCheck, disposer: DisposePropagator, wallet: Wallet, market: SerumMarket, price_watcher: Watcher[Price]) -> Watcher[Inventory]:
    base_account = TokenAccount.fetch_largest_for_owner_and_token(
        context, wallet.address, market.base)
    if base_account is None:
        raise Exception(f"Could not find token account owned by {wallet.address} for base token {market.base}.")
    base_token_subscription = WebSocketAccountSubscription[TokenAccount](
        context, base_account.address, lambda account_info: TokenAccount.parse(account_info, market.base))
    manager.add(base_token_subscription)
    latest_base_token_account_observer = LatestItemObserverSubscriber[TokenAccount](base_account)
    base_subscription_disposable = base_token_subscription.publisher.subscribe(latest_base_token_account_observer)
    disposer.add_disposable(base_subscription_disposable)

    quote_account = TokenAccount.fetch_largest_for_owner_and_token(
        context, wallet.address, market.quote)
    if quote_account is None:
        raise Exception(f"Could not find token account owned by {wallet.address} for quote token {market.quote}.")
    quote_token_subscription = WebSocketAccountSubscription[TokenAccount](
        context, quote_account.address, lambda account_info: TokenAccount.parse(account_info, market.quote))
    manager.add(quote_token_subscription)
    latest_quote_token_account_observer = LatestItemObserverSubscriber[TokenAccount](quote_account)
    quote_subscription_disposable = quote_token_subscription.publisher.subscribe(latest_quote_token_account_observer)
    disposer.add_disposable(quote_subscription_disposable)

    # Serum markets don't accrue MNGO liquidity incentives
    mngo: typing.Optional[Instrument] = context.instrument_lookup.find_by_symbol("MNGO")
    if mngo is None:
        raise Exception("Could not find details of MNGO token.")
    mngo_accrued: InstrumentValue = InstrumentValue(Token.ensure(mngo), Decimal(0))

    def serum_inventory_accessor() -> Inventory:
        available: Decimal = (latest_base_token_account_observer.latest.value.value * price_watcher.latest.mid_price) + \
            latest_quote_token_account_observer.latest.value.value
        available_collateral: InstrumentValue = InstrumentValue(
            latest_quote_token_account_observer.latest.value.token, available)
        return Inventory(InventorySource.SPL_TOKENS, mngo_accrued,
                         available_collateral,
                         latest_base_token_account_observer.latest.value,
                         latest_quote_token_account_observer.latest.value)

    return LamdaUpdateWatcher(serum_inventory_accessor)


def build_orderbook_watcher(context: Context, manager: WebSocketSubscriptionManager, health_check: HealthCheck, market: LoadedMarket) -> Watcher[OrderBook]:
    orderbook_addresses: typing.List[PublicKey] = [
        market.bids_address,
        market.asks_address
    ]
    orderbook_infos = AccountInfo.load_multiple(context, orderbook_addresses)
    if len(orderbook_infos) != 2 or orderbook_infos[0] is None or orderbook_infos[1] is None:
        raise Exception(f"Could not find {market.symbol} order book at addresses {orderbook_addresses}.")

    initial_orderbook: OrderBook = market.parse_account_infos_to_orderbook(orderbook_infos[0], orderbook_infos[1])
    updatable_orderbook: OrderBook = market.parse_account_infos_to_orderbook(
        orderbook_infos[0], orderbook_infos[1])

    def _update_bids(account_info: AccountInfo) -> OrderBook:
        new_bids = market.parse_account_info_to_orders(account_info)
        updatable_orderbook.bids = new_bids
        return updatable_orderbook

    def _update_asks(account_info: AccountInfo) -> OrderBook:
        new_asks = market.parse_account_info_to_orders(account_info)
        updatable_orderbook.asks = new_asks
        return updatable_orderbook
    bids_subscription = WebSocketAccountSubscription[OrderBook](context, orderbook_addresses[0], _update_bids)
    manager.add(bids_subscription)
    asks_subscription = WebSocketAccountSubscription[OrderBook](context, orderbook_addresses[1], _update_asks)
    manager.add(asks_subscription)

    orderbook_observer = LatestItemObserverSubscriber[OrderBook](initial_orderbook)

    bids_subscription.publisher.subscribe(orderbook_observer)
    asks_subscription.publisher.subscribe(orderbook_observer)
    health_check.add("orderbook_bids_subscription", bids_subscription.publisher)
    health_check.add("orderbook_asks_subscription", asks_subscription.publisher)
    return orderbook_observer
