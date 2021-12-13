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

import abc
import logging
import mango
import time
import typing

from decimal import Decimal
from solana.publickey import PublicKey

from ..instrumentvalue import InstrumentValue
from ..modelstate import ModelState
from ..token import Token

from ..calculators.collateralcalculator import CollateralCalculator
from ..calculators.perpcollateralcalculator import PerpCollateralCalculator
from ..calculators.spotcollateralcalculator import SpotCollateralCalculator

# # 🥭 ModelStateBuilder class
#
# Base class for building a `ModelState` through polling or websockets.
#


class ModelStateBuilder(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def build(self, context: mango.Context) -> ModelState:
        raise NotImplementedError("ModelStateBuilder.build() is not implemented on the base type.")

    def __str__(self) -> str:
        return "« ModelStateBuilder »"

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 WebsocketModelStateBuilder class
#
# Base class for building a `ModelState` through polling.
#
class WebsocketModelStateBuilder(ModelStateBuilder):
    def __init__(self, model_state: ModelState) -> None:
        super().__init__()
        self.model_state: ModelState = model_state

    def build(self, context: mango.Context) -> ModelState:
        return self.model_state

    def __str__(self) -> str:
        return f"« WebsocketModelStateBuilder for market '{self.model_state.market.symbol}' »"


# # 🥭 PollingModelStateBuilder class
#
# Base class for building a `ModelState` through polling.
#
class PollingModelStateBuilder(ModelStateBuilder):
    def __init__(self) -> None:
        super().__init__()

    def build(self, context: mango.Context) -> ModelState:
        started_at = time.time()
        built: ModelState = self.poll(context)
        time_taken = time.time() - started_at
        self._logger.debug(f"Poll for model state complete. Time taken: {time_taken:.2f} seconds.")
        return built

    @abc.abstractmethod
    def poll(self, context: mango.Context) -> ModelState:
        raise NotImplementedError("PollingModelStateBuilder.poll() is not implemented on the base type.")

    def from_values(self, order_owner: PublicKey, market: mango.Market, group: mango.Group, account: mango.Account,
                    price: mango.Price, placed_orders_container: mango.PlacedOrdersContainer,
                    inventory: mango.Inventory, orderbook: mango.OrderBook) -> ModelState:
        group_watcher: mango.ManualUpdateWatcher[mango.Group] = mango.ManualUpdateWatcher(group)
        account_watcher: mango.ManualUpdateWatcher[mango.Account] = mango.ManualUpdateWatcher(account)
        price_watcher: mango.ManualUpdateWatcher[mango.Price] = mango.ManualUpdateWatcher(price)
        placed_orders_container_watcher: mango.ManualUpdateWatcher[
            mango.PlacedOrdersContainer] = mango.ManualUpdateWatcher(placed_orders_container)
        inventory_watcher: mango.ManualUpdateWatcher[mango.Inventory] = mango.ManualUpdateWatcher(inventory)
        orderbook_watcher: mango.ManualUpdateWatcher[mango.OrderBook] = mango.ManualUpdateWatcher(orderbook)

        return ModelState(order_owner, market, group_watcher, account_watcher, price_watcher,
                          placed_orders_container_watcher, inventory_watcher, orderbook_watcher)

    def __str__(self) -> str:
        return "« PollingModelStateBuilder »"


# # 🥭 SerumPollingModelStateBuilder class
#
# Polls Solana and builds a `ModelState` for a `SerumMarket`
#
class SerumPollingModelStateBuilder(PollingModelStateBuilder):
    def __init__(self,
                 order_owner: PublicKey,
                 market: mango.SerumMarket,
                 oracle: mango.Oracle,
                 group_address: PublicKey,
                 cache_address: PublicKey,
                 account_address: PublicKey,
                 open_orders_address: PublicKey,
                 base_inventory_token_account: mango.TokenAccount,
                 quote_inventory_token_account: mango.TokenAccount,
                 ) -> None:
        super().__init__()
        self.order_owner: PublicKey = order_owner
        self.market: mango.SerumMarket = market
        self.oracle: mango.Oracle = oracle

        self.group_address: PublicKey = group_address
        self.cache_address: PublicKey = cache_address
        self.account_address: PublicKey = account_address
        self.open_orders_address: PublicKey = open_orders_address
        self.base_inventory_token_account: mango.TokenAccount = base_inventory_token_account
        self.quote_inventory_token_account: mango.TokenAccount = quote_inventory_token_account

        # Serum always uses Tokens
        self.base_token: Token = Token.ensure(self.base_inventory_token_account.value.token)
        self.quote_token: Token = Token.ensure(self.quote_inventory_token_account.value.token)

    def poll(self, context: mango.Context) -> ModelState:
        addresses: typing.List[PublicKey] = [
            self.group_address,
            self.cache_address,
            self.account_address,
            self.open_orders_address,
            self.base_inventory_token_account.address,
            self.quote_inventory_token_account.address,
            self.market.bids_address,
            self.market.asks_address
        ]
        account_infos: typing.Sequence[mango.AccountInfo] = mango.AccountInfo.load_multiple(context, addresses)
        group: mango.Group = mango.Group.parse_with_context(context, account_infos[0])
        cache: mango.Cache = mango.Cache.parse(account_infos[1])
        account: mango.Account = mango.Account.parse(account_infos[2], group, cache)
        placed_orders_container: mango.PlacedOrdersContainer = mango.OpenOrders.parse(
            account_infos[3], self.market.base.decimals, self.market.quote.decimals)

        # Serum markets don't accrue MNGO liquidity incentives
        mngo_accrued: InstrumentValue = InstrumentValue(group.liquidity_incentive_token, Decimal(0))

        base_inventory_token_account = mango.TokenAccount.parse(account_infos[4], self.base_token)
        quote_inventory_token_account = mango.TokenAccount.parse(account_infos[5], self.quote_token)

        orderbook: mango.OrderBook = self.market.parse_account_infos_to_orderbook(account_infos[6], account_infos[7])

        price: mango.Price = self.oracle.fetch_price(context)

        available: Decimal = (base_inventory_token_account.value.value * price.mid_price) + \
            quote_inventory_token_account.value.value
        available_collateral: InstrumentValue = InstrumentValue(quote_inventory_token_account.value.token, available)
        inventory: mango.Inventory = mango.Inventory(mango.InventorySource.SPL_TOKENS,
                                                     mngo_accrued,
                                                     available_collateral,
                                                     base_inventory_token_account.value,
                                                     quote_inventory_token_account.value)

        return self.from_values(self.order_owner, self.market, group, account, price, placed_orders_container, inventory, orderbook)

    def __str__(self) -> str:
        return f"""« SerumPollingModelStateBuilder for market '{self.market.symbol}' »"""


# # 🥭 SpotPollingModelStateBuilder class
#
# Polls Solana and builds a `ModelState` for a `SpotMarket`
#
class SpotPollingModelStateBuilder(PollingModelStateBuilder):
    def __init__(self,
                 order_owner: PublicKey,
                 market: mango.SpotMarket,
                 oracle: mango.Oracle,
                 group_address: PublicKey,
                 cache_address: PublicKey,
                 account_address: PublicKey,
                 open_orders_address: PublicKey,
                 all_open_orders_addresses: typing.Sequence[PublicKey]
                 ) -> None:
        super().__init__()
        self.order_owner: PublicKey = order_owner
        self.market: mango.SpotMarket = market
        self.oracle: mango.Oracle = oracle

        self.group_address: PublicKey = group_address
        self.cache_address: PublicKey = cache_address
        self.account_address: PublicKey = account_address
        self.open_orders_address: PublicKey = open_orders_address
        self.all_open_orders_addresses: typing.Sequence[PublicKey] = all_open_orders_addresses

        self.collateral_calculator: CollateralCalculator = SpotCollateralCalculator()

    def poll(self, context: mango.Context) -> ModelState:
        addresses: typing.List[PublicKey] = [
            self.group_address,
            self.cache_address,
            self.account_address,
            self.market.bids_address,
            self.market.asks_address,
            *self.all_open_orders_addresses
        ]
        account_infos: typing.Sequence[mango.AccountInfo] = mango.AccountInfo.load_multiple(context, addresses)
        group: mango.Group = mango.Group.parse_with_context(context, account_infos[0])
        cache: mango.Cache = mango.Cache.parse(account_infos[1])
        account: mango.Account = mango.Account.parse(account_infos[2], group, cache)

        # Update our stash of OpenOrders addresses for next time, in case new OpenOrders accounts were added
        self.all_open_orders_addresses = account.spot_open_orders

        spot_open_orders_account_infos_by_address = {
            str(account_info.address): account_info for account_info in account_infos[5:]}

        all_open_orders: typing.Dict[str, mango.OpenOrders] = {}
        for basket_token in account.slots:
            if basket_token.spot_open_orders is not None and str(basket_token.spot_open_orders) in spot_open_orders_account_infos_by_address:
                account_info: mango.AccountInfo = spot_open_orders_account_infos_by_address[str(
                    basket_token.spot_open_orders)]
                open_orders: mango.OpenOrders = mango.OpenOrders.parse(
                    account_info,
                    basket_token.base_instrument.decimals,
                    account.shared_quote_token.decimals)
                all_open_orders[str(basket_token.spot_open_orders)] = open_orders

        placed_orders_container: mango.PlacedOrdersContainer = all_open_orders[str(self.open_orders_address)]

        # Spot markets don't accrue MNGO liquidity incentives
        mngo_accrued: InstrumentValue = InstrumentValue(group.liquidity_incentive_token, Decimal(0))

        base_value = mango.InstrumentValue.find_by_symbol(account.net_values, self.market.base.symbol)
        quote_value = mango.InstrumentValue.find_by_symbol(account.net_values, self.market.quote.symbol)

        available_collateral: InstrumentValue = self.collateral_calculator.calculate(
            account, all_open_orders, group, cache)
        inventory: mango.Inventory = mango.Inventory(mango.InventorySource.ACCOUNT,
                                                     mngo_accrued,
                                                     available_collateral,
                                                     base_value,
                                                     quote_value)

        orderbook: mango.OrderBook = self.market.parse_account_infos_to_orderbook(account_infos[3], account_infos[4])

        price: mango.Price = self.oracle.fetch_price(context)

        return self.from_values(self.order_owner, self.market, group, account, price, placed_orders_container, inventory, orderbook)

    def __str__(self) -> str:
        return f"""« SpotPollingModelStateBuilder for market '{self.market.symbol}' »"""


# # 🥭 PerpPollingModelStateBuilder class
#
# Polls Solana and builds a `ModelState` for a `PerpMarket`
#
class PerpPollingModelStateBuilder(PollingModelStateBuilder):
    def __init__(self,
                 order_owner: PublicKey,
                 market: mango.PerpMarket,
                 oracle: mango.Oracle,
                 group_address: PublicKey,
                 cache_address: PublicKey,
                 account_address: PublicKey
                 ) -> None:
        super().__init__()
        self.order_owner: PublicKey = order_owner
        self.market: mango.PerpMarket = market
        self.oracle: mango.Oracle = oracle

        self.group_address: PublicKey = group_address
        self.cache_address: PublicKey = cache_address
        self.account_address: PublicKey = account_address

        self.collateral_calculator: CollateralCalculator = PerpCollateralCalculator()

    def poll(self, context: mango.Context) -> ModelState:
        addresses: typing.List[PublicKey] = [
            self.group_address,
            self.cache_address,
            self.account_address,
            self.market.underlying_perp_market.bids,
            self.market.underlying_perp_market.asks
        ]
        account_infos: typing.Sequence[mango.AccountInfo] = mango.AccountInfo.load_multiple(context, addresses)
        group: mango.Group = mango.Group.parse_with_context(context, account_infos[0])
        cache: mango.Cache = mango.Cache.parse(account_infos[1])
        account: mango.Account = mango.Account.parse(account_infos[2], group, cache)

        slot = group.slot_by_perp_market_address(self.market.address)
        perp_account = account.perp_accounts_by_index[slot.index]
        if perp_account is None:
            raise Exception(f"Could not find perp account at index {slot.index} of account {account.address}.")
        placed_orders_container: mango.PlacedOrdersContainer = perp_account.open_orders

        base_lots = perp_account.base_position
        base_value = self.market.lot_size_converter.base_size_lots_to_number(base_lots)
        base_token_value = mango.InstrumentValue(self.market.base, base_value)
        quote_token_value = account.shared_quote.net_value
        available_collateral: InstrumentValue = self.collateral_calculator.calculate(account, {}, group, cache)
        inventory: mango.Inventory = mango.Inventory(mango.InventorySource.ACCOUNT,
                                                     perp_account.mngo_accrued,
                                                     available_collateral,
                                                     base_token_value,
                                                     quote_token_value)

        orderbook: mango.OrderBook = self.market.parse_account_infos_to_orderbook(account_infos[3], account_infos[4])

        price: mango.Price = self.oracle.fetch_price(context)

        return self.from_values(self.order_owner, self.market, group, account, price, placed_orders_container, inventory, orderbook)

    def __str__(self) -> str:
        return f"""« PerpPollingModelStateBuilder for market '{self.market.symbol}' »"""
