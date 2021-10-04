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

from ..modelstate import ModelState
from ..tokenvalue import TokenValue

from ..calculators.collateralcalculator import CollateralCalculator
from ..calculators.perpcollateralcalculator import PerpCollateralCalculator
from ..calculators.spotcollateralcalculator import SpotCollateralCalculator

# # 🥭 ModelStateBuilder class
#
# Base class for building a `ModelState` through polling or websockets.
#


class ModelStateBuilder(metaclass=abc.ABCMeta):
    def __init__(self):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def build(self, context: mango.Context) -> ModelState:
        raise NotImplementedError("ModelStateBuilder.build() is not implemented on the base type.")

    def __str__(self) -> str:
        return "« 𝙼𝚘𝚍𝚎𝚕𝚂𝚝𝚊𝚝𝚎𝙱𝚞𝚒𝚕𝚍𝚎𝚛 »"

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 WebsocketModelStateBuilder class
#
# Base class for building a `ModelState` through polling.
#
class WebsocketModelStateBuilder(ModelStateBuilder):
    def __init__(self, model_state: ModelState):
        super().__init__()
        self.model_state: ModelState = model_state

    def build(self, context: mango.Context) -> ModelState:
        return self.model_state

    def __str__(self) -> str:
        return f"« 𝚆𝚎𝚋𝚜𝚘𝚌𝚔𝚎𝚝𝙼𝚘𝚍𝚎𝚕𝚂𝚝𝚊𝚝𝚎𝙱𝚞𝚒𝚕𝚍𝚎𝚛 for market '{self.model_state.market.symbol}' »"


# # 🥭 PollingModelStateBuilder class
#
# Base class for building a `ModelState` through polling.
#
class PollingModelStateBuilder(ModelStateBuilder):
    def __init__(self):
        super().__init__()

    def build(self, context: mango.Context) -> ModelState:
        started_at = time.time()
        built: ModelState = self.poll(context)
        time_taken = time.time() - started_at
        self.logger.debug(f"Poll for model state complete. Time taken: {time_taken:.2f} seconds.")
        return built

    @abc.abstractmethod
    def poll(self, context: mango.Context) -> ModelState:
        raise NotImplementedError("PollingModelStateBuilder.poll() is not implemented on the base type.")

    def from_values(self, order_owner: PublicKey, market: mango.Market, group: mango.Group, account: mango.Account,
                    price: mango.Price, placed_orders_container: mango.PlacedOrdersContainer,
                    inventory: mango.Inventory, bids: typing.Sequence[mango.Order],
                    asks: typing.Sequence[mango.Order]) -> ModelState:
        group_watcher: mango.ManualUpdateWatcher[mango.Group] = mango.ManualUpdateWatcher(group)
        account_watcher: mango.ManualUpdateWatcher[mango.Account] = mango.ManualUpdateWatcher(account)
        price_watcher: mango.ManualUpdateWatcher[mango.Price] = mango.ManualUpdateWatcher(price)
        placed_orders_container_watcher: mango.ManualUpdateWatcher[
            mango.PlacedOrdersContainer] = mango.ManualUpdateWatcher(placed_orders_container)
        inventory_watcher: mango.ManualUpdateWatcher[mango.Inventory] = mango.ManualUpdateWatcher(inventory)
        bids_watcher: mango.ManualUpdateWatcher[typing.Sequence[mango.Order]] = mango.ManualUpdateWatcher(bids)
        asks_watcher: mango.ManualUpdateWatcher[typing.Sequence[mango.Order]] = mango.ManualUpdateWatcher(asks)

        return ModelState(order_owner, market, group_watcher, account_watcher, price_watcher,
                          placed_orders_container_watcher, inventory_watcher, bids_watcher, asks_watcher)

    def __str__(self) -> str:
        return "« 𝙿𝚘𝚕𝚕𝚒𝚗𝚐𝙼𝚘𝚍𝚎𝚕𝚂𝚝𝚊𝚝𝚎𝙱𝚞𝚒𝚕𝚍𝚎𝚛 »"


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
                 account_address: PublicKey,
                 open_orders_address: PublicKey,
                 base_inventory_token_account: mango.TokenAccount,
                 quote_inventory_token_account: mango.TokenAccount,
                 ):
        super().__init__()
        self.order_owner: PublicKey = order_owner
        self.market: mango.SerumMarket = market
        self.oracle: mango.Oracle = oracle

        self.group_address: PublicKey = group_address
        self.account_address: PublicKey = account_address
        self.open_orders_address: PublicKey = open_orders_address
        self.base_inventory_token_account: mango.TokenAccount = base_inventory_token_account
        self.quote_inventory_token_account: mango.TokenAccount = quote_inventory_token_account

    def poll(self, context: mango.Context) -> ModelState:
        addresses: typing.List[PublicKey] = [
            self.group_address,
            self.account_address,
            self.open_orders_address,
            self.base_inventory_token_account.address,
            self.quote_inventory_token_account.address,
            self.market.underlying_serum_market.state.bids(),
            self.market.underlying_serum_market.state.asks()
        ]
        account_infos: typing.Sequence[mango.AccountInfo] = mango.AccountInfo.load_multiple(context, addresses)
        group: mango.Group = mango.Group.parse(context, account_infos[0])
        account: mango.Account = mango.Account.parse(account_infos[1], group)
        placed_orders_container: mango.PlacedOrdersContainer = mango.OpenOrders.parse(
            account_infos[2], self.market.base.decimals, self.market.quote.decimals)

        # Serum markets don't accrue MNGO liquidity incentives
        mngo = group.find_token_info_by_symbol("MNGO").token
        mngo_accrued: TokenValue = TokenValue(mngo, Decimal(0))

        base_inventory_token_account = mango.TokenAccount.parse(
            account_infos[3], self.base_inventory_token_account.value.token)
        quote_inventory_token_account = mango.TokenAccount.parse(
            account_infos[4], self.quote_inventory_token_account.value.token)

        # Both these will have top-of-book at index 0.
        bids: typing.Sequence[mango.Order] = mango.parse_account_info_to_orders(
            account_infos[5], self.market.underlying_serum_market)
        asks: typing.Sequence[mango.Order] = mango.parse_account_info_to_orders(
            account_infos[6], self.market.underlying_serum_market)

        price: mango.Price = self.oracle.fetch_price(context)

        available: Decimal = (base_inventory_token_account.value.value * price.mid_price) + \
            quote_inventory_token_account.value.value
        available_collateral: TokenValue = TokenValue(quote_inventory_token_account.value.token, available)
        inventory: mango.Inventory = mango.Inventory(mango.InventorySource.SPL_TOKENS,
                                                     mngo_accrued,
                                                     available_collateral,
                                                     base_inventory_token_account.value,
                                                     quote_inventory_token_account.value)

        return self.from_values(self.order_owner, self.market, group, account, price, placed_orders_container, inventory, bids, asks)

    def __str__(self) -> str:
        return f"""« 𝚂𝚎𝚛𝚞𝚖𝙿𝚘𝚕𝚕𝚒𝚗𝚐𝙼𝚘𝚍𝚎𝚕𝚂𝚝𝚊𝚝𝚎𝙱𝚞𝚒𝚕𝚍𝚎𝚛 for market '{self.market.symbol}' »"""


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
                 ):
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
            self.market.underlying_serum_market.state.bids(),
            self.market.underlying_serum_market.state.asks(),
            *self.all_open_orders_addresses
        ]
        account_infos: typing.Sequence[mango.AccountInfo] = mango.AccountInfo.load_multiple(context, addresses)
        group: mango.Group = mango.Group.parse(context, account_infos[0])
        cache: mango.Cache = mango.Cache.parse(account_infos[1])
        account: mango.Account = mango.Account.parse(account_infos[2], group)

        # Update our stash of OpenOrders addresses for next time, in case new OpenOrders accounts were added
        self.all_open_orders_addresses = list([oo for oo in account.spot_open_orders if oo is not None])

        spot_open_orders_account_infos_by_address = {
            str(account_info.address): account_info for account_info in account_infos[5:]}

        all_open_orders: typing.Dict[str, mango.OpenOrders] = {}
        for basket_token in account.basket:
            if basket_token.spot_open_orders is not None and str(basket_token.spot_open_orders) in spot_open_orders_account_infos_by_address:
                account_info: mango.AccountInfo = spot_open_orders_account_infos_by_address[str(
                    basket_token.spot_open_orders)]
                open_orders: mango.OpenOrders = mango.OpenOrders.parse(
                    account_info,
                    basket_token.token_info.decimals,
                    account.shared_quote_token.token_info.token.decimals)
                all_open_orders[str(basket_token.spot_open_orders)] = open_orders

        placed_orders_container: mango.PlacedOrdersContainer = all_open_orders[str(self.open_orders_address)]

        # Spot markets don't accrue MNGO liquidity incentives
        mngo = group.find_token_info_by_symbol("MNGO").token
        mngo_accrued: TokenValue = TokenValue(mngo, Decimal(0))

        base_value = mango.TokenValue.find_by_symbol(account.net_assets, self.market.base.symbol)
        quote_value = mango.TokenValue.find_by_symbol(account.net_assets, self.market.quote.symbol)

        available_collateral: TokenValue = self.collateral_calculator.calculate(account, all_open_orders, group, cache)
        inventory: mango.Inventory = mango.Inventory(mango.InventorySource.ACCOUNT,
                                                     mngo_accrued,
                                                     available_collateral,
                                                     base_value,
                                                     quote_value)

        # Both these will have top-of-book at index 0.
        bids: typing.Sequence[mango.Order] = mango.parse_account_info_to_orders(
            account_infos[3], self.market.underlying_serum_market)
        asks: typing.Sequence[mango.Order] = mango.parse_account_info_to_orders(
            account_infos[4], self.market.underlying_serum_market)

        price: mango.Price = self.oracle.fetch_price(context)

        return self.from_values(self.order_owner, self.market, group, account, price, placed_orders_container, inventory, bids, asks)

    def __str__(self) -> str:
        return f"""« 𝚂𝚙𝚘𝚝𝙿𝚘𝚕𝚕𝚒𝚗𝚐𝙼𝚘𝚍𝚎𝚕𝚂𝚝𝚊𝚝𝚎𝙱𝚞𝚒𝚕𝚍𝚎𝚛 for market '{self.market.symbol}' »"""


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
                 ):
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
        group: mango.Group = mango.Group.parse(context, account_infos[0])
        cache: mango.Cache = mango.Cache.parse(account_infos[1])
        account: mango.Account = mango.Account.parse(account_infos[2], group)

        index = group.find_perp_market_index(self.market.address)
        perp_account = account.perp_accounts[index]
        if perp_account is None:
            raise Exception(f"Could not find perp account at index {index} of account {account.address}.")
        placed_orders_container: mango.PlacedOrdersContainer = perp_account.open_orders

        base_lots = perp_account.base_position
        base_value = self.market.lot_size_converter.base_size_lots_to_number(base_lots)
        base_token_value = mango.TokenValue(self.market.base, base_value)
        quote_token_value = mango.TokenValue.find_by_symbol(account.net_assets, self.market.quote.symbol)
        available_collateral: TokenValue = self.collateral_calculator.calculate(account, {}, group, cache)
        inventory: mango.Inventory = mango.Inventory(mango.InventorySource.ACCOUNT,
                                                     perp_account.mngo_accrued,
                                                     available_collateral,
                                                     base_token_value,
                                                     quote_token_value)

        # Both these will have top-of-book at index 0.
        bids: mango.PerpOrderBookSide = mango.PerpOrderBookSide.parse(
            context, account_infos[3], self.market.underlying_perp_market)
        asks: mango.PerpOrderBookSide = mango.PerpOrderBookSide.parse(
            context, account_infos[4], self.market.underlying_perp_market)

        price: mango.Price = self.oracle.fetch_price(context)

        return self.from_values(self.order_owner, self.market, group, account, price, placed_orders_container, inventory, bids.orders(), asks.orders())

    def __str__(self) -> str:
        return f"""« 𝙿𝚎𝚛𝚙𝙿𝚘𝚕𝚕𝚒𝚗𝚐𝙼𝚘𝚍𝚎𝚕𝚂𝚝𝚊𝚝𝚎𝙱𝚞𝚒𝚕𝚍𝚎𝚛 for market '{self.market.symbol}' »"""
