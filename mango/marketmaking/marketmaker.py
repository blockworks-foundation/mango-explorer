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
import mango
import traceback
import typing

from decimal import Decimal
from mango.marketmaking.modelstate import ModelState


# # 🥭 SimpleMarketMaker class
#
# An event-driven market-maker.
#

class MarketMaker:
    def __init__(self, wallet: mango.Wallet, market: mango.Market,
                 spread_ratio: Decimal, position_size_ratio: Decimal):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.wallet: mango.Wallet = wallet
        self.market: mango.Market = market
        self.spread_ratio: Decimal = spread_ratio
        self.position_size_ratio: Decimal = position_size_ratio
        self.buys = []
        self.sells = []

    def calculate_order_prices(self, model_state: ModelState):
        price: mango.Price = model_state.price
        bid = price.mid_price - (price.mid_price * self.spread_ratio)
        ask = price.mid_price + (price.mid_price * self.spread_ratio)

        return (bid, ask)

    def calculate_order_sizes(self, model_state: ModelState):
        price: mango.Price = model_state.price
        inventory: typing.Sequence[typing.Optional[mango.TokenValue]] = model_state.account.net_assets
        base_tokens: typing.Optional[mango.TokenValue] = mango.TokenValue.find_by_token(inventory, price.market.base)
        if base_tokens is None:
            raise Exception(f"Could not find market-maker base token {price.market.base.symbol} in inventory.")

        quote_tokens: typing.Optional[mango.TokenValue] = mango.TokenValue.find_by_token(inventory, price.market.quote)
        if quote_tokens is None:
            raise Exception(f"Could not find market-maker quote token {price.market.quote.symbol} in inventory.")

        total = (base_tokens.value * price.mid_price) + quote_tokens.value
        position_size = total * self.position_size_ratio

        buy_size = position_size / price.mid_price
        sell_size = position_size / price.mid_price
        return (buy_size, sell_size)

    def pulse_perp(self, context: mango.Context, model_state: ModelState):
        try:
            bid, ask = self.calculate_order_prices(model_state)
            buy_size, sell_size = self.calculate_order_sizes(model_state)
            payer = mango.InstructionData.from_wallet(self.wallet)
            perp_market = model_state.perp_market
            perp_account = model_state.account.perp_accounts[perp_market.market_index]

            cancellations = mango.InstructionData.empty()
            print("Client IDs", [client_id for client_id in perp_account.open_orders.client_order_ids if client_id != 0])
            for client_order_id in perp_account.open_orders.client_order_ids:
                if client_order_id != 0:
                    self.logger.info(f"Cancelling order with client ID: {client_order_id}")
                    order = mango.Order(id=0, client_id=client_order_id, owner=self.wallet.address,
                                        side=mango.Side.BUY, price=Decimal(0), size=Decimal(0))
                    cancel = mango.build_cancel_perp_order_instructions(
                        context, self.wallet, model_state.account, perp_market, order)
                    cancellations += cancel

            buy_client_id = context.random_client_id()
            buy = mango.build_place_perp_order_instructions(
                context, self.wallet, model_state.group, model_state.account, perp_market, bid, buy_size, buy_client_id, mango.Side.BUY, mango.OrderType.LIMIT)
            self.logger.info(f"Placing BUY order for {buy_size} at price {bid} with client ID: {buy_client_id}")

            sell_client_id = context.random_client_id()
            sell = mango.build_place_perp_order_instructions(
                context, self.wallet, model_state.group, model_state.account, perp_market, ask, sell_size, sell_client_id, mango.Side.SELL, mango.OrderType.LIMIT)
            self.logger.info(f"Placing SELL order for {sell_size} at price {ask} with client ID: {sell_client_id}")

            crank = mango.build_mango_consume_events_instructions(
                context, self.wallet, model_state.group, model_state.account, model_state.perp_market)
            (payer + cancellations + buy + sell + crank).execute(context)
        except Exception as exception:
            self.logger.error(f"Market-maker error on pulse: {exception} - {traceback.format_exc()}")

    def pulse_spot(self, context: mango.Context, model_state: ModelState):
        try:
            bid, ask = self.calculate_order_prices(model_state)
            buy_size, sell_size = self.calculate_order_sizes(model_state)
            payer = mango.InstructionData.from_wallet(self.wallet)

            srm = context.token_lookup.find_by_symbol("SRM")
            if srm is None:
                fee_discount_token_account_address = None
            else:
                fee_discount_token_account = mango.TokenAccount.fetch_largest_for_owner_and_token(
                    context, self.wallet.address, srm)
                fee_discount_token_account_address = fee_discount_token_account.address

            cancellations = mango.InstructionData.empty()
            for order_id in model_state.spot_open_orders.orders:
                if order_id != 0:
                    side = mango.Side.BUY if order_id in self.buys else mango.Side.SELL
                    self.logger.info(f"Cancelling order with client ID: {order_id}")
                    order = mango.Order(id=order_id, client_id=0, owner=self.wallet.address,
                                        side=mango.Side.BUY, price=Decimal(0), size=Decimal(0))
                    cancel = mango.build_cancel_spot_order_instructions(
                        context, self.wallet, model_state.group, model_state.account, model_state.spot_market, order, model_state.spot_open_orders.address)
                    cancellations += cancel

            buy_client_id = context.random_client_id()
            buy = mango.build_spot_place_order_instructions(context, self.wallet, model_state.group,
                                                            model_state.account, model_state.spot_market,
                                                            mango.OrderType.LIMIT,
                                                            mango.Side.BUY, bid, buy_size, buy_client_id,
                                                            fee_discount_token_account_address)
            self.buys += [buy_client_id]
            self.logger.info(f"Placing BUY order for {buy_size} at price {bid} with client ID: {buy_client_id}")

            sell_client_id = context.random_client_id()
            sell = mango.build_spot_place_order_instructions(context, self.wallet, model_state.group,
                                                             model_state.account, model_state.spot_market,
                                                             mango.OrderType.LIMIT,
                                                             mango.Side.SELL, ask, sell_size, sell_client_id,
                                                             fee_discount_token_account_address)
            self.sells += [sell_client_id]
            self.logger.info(f"Placing SELL order for {sell_size} at price {ask} with client ID: {sell_client_id}")

            open_orders_addresses = list([oo for oo in model_state.account.spot_open_orders if oo is not None])
            crank = mango.build_serum_consume_events_instructions(
                context, self.wallet, model_state.spot_market, open_orders_addresses)
            (payer + cancellations + buy + sell + crank).execute(context)
        except Exception as exception:
            self.logger.error(f"Market-maker error on pulse: {exception} - {traceback.format_exc()}")

    def __str__(self) -> str:
        return f"""« 𝙼𝚊𝚛𝚔𝚎𝚝𝙼𝚊𝚔𝚎𝚛 for market '{self.market.symbol}' »"""

    def __repr__(self) -> str:
        return f"{self}"
