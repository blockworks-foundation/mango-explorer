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

import typing

from decimal import Decimal

from ..account import Account
from ..cache import Cache
from ..group import GroupSlotSpotMarket, GroupSlotPerpMarket, GroupSlot, Group
from ..instrumentvalue import InstrumentValue
from ..openorders import OpenOrders

from .collateralcalculator import CollateralCalculator


class SpotCollateralCalculator(CollateralCalculator):
    def __init__(self) -> None:
        super().__init__()

    # From Daffy in Discord, 30th August 2021 (https://discord.com/channels/791995070613159966/807051268304273408/882029587914182666)
    #   I think the correct calculation is
    #   total_collateral = deposits[QUOTE_INDEX] * deposit_index         - borrows[QUOTE_INDEX] * borrow_index
    #   for i in num_oracles:
    #     total_collateral += prices[i] * (init_asset_weights[i] * deposits[i] * deposit_index -  init_liab_weights[i] * borrows[i] * borrow_index)
    #
    # Also from Daffy, same thread, when I said there were two `init_asset_weights`, one for spot and one for perp (https://discord.com/channels/791995070613159966/807051268304273408/882030633940054056):
    #   yes I think we ignore perps
    #
    def calculate(self, account: Account, all_open_orders: typing.Dict[str, OpenOrders], group: Group, cache: Cache) -> InstrumentValue:
        # Quote token calculation:
        #   total_collateral = deposits[QUOTE_INDEX] * deposit_index - borrows[QUOTE_INDEX] * borrow_index
        # Note: the `AccountSlot` in the `Account` already factors the deposit and borrow index.
        total: Decimal = account.shared_quote.net_value.value
        collateral_description = [f"{total:,.8f} USDC"]
        for basket_token in account.base_slots:
            slot: GroupSlot = group.slot_by_instrument(basket_token.base_instrument)
            token_price = group.token_price_from_cache(cache, basket_token.base_instrument)

            spot_market: typing.Optional[GroupSlotSpotMarket] = slot.spot_market
            init_asset_weight: Decimal
            init_liab_weight: Decimal
            if spot_market is not None:
                init_asset_weight = spot_market.init_asset_weight
                init_liab_weight = spot_market.init_liab_weight
            else:
                perp_market: typing.Optional[GroupSlotPerpMarket] = slot.perp_market
                if perp_market is None:
                    raise Exception(
                        f"Could not read spot or perp market of token {basket_token.base_instrument.symbol} at index {slot.index} of cache at {cache.address}")
                init_asset_weight = perp_market.init_asset_weight
                init_liab_weight = perp_market.init_liab_weight

            in_orders: Decimal = Decimal(0)
            if basket_token.spot_open_orders is not None and str(basket_token.spot_open_orders) in all_open_orders:
                open_orders: OpenOrders = all_open_orders[str(basket_token.spot_open_orders)]
                in_orders = open_orders.quote_token_total + \
                    (open_orders.base_token_total * token_price.value * init_asset_weight)

            # Base token calculations:
            #     total_collateral += prices[i] * (init_asset_weights[i] * deposits[i] * deposit_index -  init_liab_weights[i] * borrows[i] * borrow_index)
            # Note: the `AccountSlot` in the `Account` already factors the deposit and borrow index.
            weighted: Decimal = in_orders + (token_price.value * ((
                basket_token.deposit.value * init_asset_weight) - (
                    basket_token.borrow.value * init_liab_weight)))

            if weighted != 0:
                collateral_description += [f"{weighted:,.8f} USDC from {basket_token.base_instrument.symbol}"]
                total += weighted

        self._logger.debug(f"Weighted collateral: {', '.join(collateral_description)}")
        return InstrumentValue(group.shared_quote_token, total)
