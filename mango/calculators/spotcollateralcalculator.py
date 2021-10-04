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
from ..cache import Cache, PriceCache
from ..group import Group
from ..openorders import OpenOrders
from ..spotmarketinfo import SpotMarketInfo
from ..tokenvalue import TokenValue

from .collateralcalculator import CollateralCalculator


class SpotCollateralCalculator(CollateralCalculator):
    def __init__(self):
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
    def calculate(self, account: Account, all_open_orders: typing.Dict[str, OpenOrders], group: Group, cache: Cache) -> TokenValue:
        # Quote token calculation:
        #   total_collateral = deposits[QUOTE_INDEX] * deposit_index - borrows[QUOTE_INDEX] * borrow_index
        # Note: the `AccountBasketToken` in the `Account` already factors the deposit and borrow index.
        total: Decimal = account.shared_quote_token.net_value.value
        for basket_token in account.basket:
            index = group.find_base_token_market_index(basket_token.token_info)
            token_price: typing.Optional[PriceCache] = cache.price_cache[index]
            if token_price is None:
                raise Exception(
                    f"Could not read price of token {basket_token.token_info.token.symbol} at index {index} of cache at {cache.address}")
            spot_market: typing.Optional[SpotMarketInfo] = group.spot_markets[index]
            if spot_market is None:
                raise Exception(
                    f"Could not read spot market of token {basket_token.token_info.token.symbol} at index {index} of cache at {cache.address}")

            in_orders: Decimal = Decimal(0)
            if basket_token.spot_open_orders is not None and str(basket_token.spot_open_orders) in all_open_orders:
                open_orders: OpenOrders = all_open_orders[str(basket_token.spot_open_orders)]
                in_orders = open_orders.quote_token_total + \
                    (open_orders.base_token_total * token_price.price * spot_market.init_asset_weight)

            # Base token calculations:
            #     total_collateral += prices[i] * (init_asset_weights[i] * deposits[i] * deposit_index -  init_liab_weights[i] * borrows[i] * borrow_index)
            # Note: the `AccountBasketToken` in the `Account` already factors the deposit and borrow index.
            weighted: Decimal = in_orders + (token_price.price * ((
                basket_token.deposit.value * spot_market.init_asset_weight) - (
                    basket_token.borrow.value * spot_market.init_liab_weight)))
            total += weighted

        return TokenValue(group.shared_quote_token.token, total)
