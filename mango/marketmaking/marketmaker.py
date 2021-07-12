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


# # 🥭 MarketMaker class
#
# An event-driven market-maker.
#

class MarketMaker:
    def __init__(self, wallet: mango.Wallet, market: mango.Market,
                 market_instruction_builder: mango.MarketInstructionBuilder,
                 spread_ratio: Decimal, position_size_ratio: Decimal):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.wallet: mango.Wallet = wallet
        self.market: mango.Market = market
        self.market_instruction_builder: mango.MarketInstructionBuilder = market_instruction_builder
        self.spread_ratio: Decimal = spread_ratio
        self.position_size_ratio: Decimal = position_size_ratio
        self.buy_client_ids: typing.List[int] = []
        self.sell_client_ids: typing.List[int] = []

    def calculate_order_prices(self, model_state: ModelState) -> typing.Tuple[Decimal, Decimal]:
        price: mango.Price = model_state.price
        bid: Decimal = price.mid_price - (price.mid_price * self.spread_ratio)
        ask: Decimal = price.mid_price + (price.mid_price * self.spread_ratio)

        return (bid, ask)

    def calculate_order_sizes(self, model_state: ModelState) -> typing.Tuple[Decimal, Decimal]:
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

        buy_size: Decimal = position_size / price.mid_price
        sell_size: Decimal = position_size / price.mid_price
        return (buy_size, sell_size)

    def pulse(self, context: mango.Context, model_state: ModelState):
        try:
            bid, ask = self.calculate_order_prices(model_state)
            buy_size, sell_size = self.calculate_order_sizes(model_state)
            payer = mango.CombinableInstructions.from_wallet(self.wallet)

            cancellations = mango.CombinableInstructions.empty()
            for order_id, client_id in model_state.placed_order_ids:
                if client_id != 0:
                    self.logger.info(f"Cancelling order with client ID: {client_id}")
                    side = mango.Side.BUY if client_id in self.buy_client_ids else mango.Side.SELL
                    order = mango.Order(id=int(order_id), client_id=int(client_id), owner=self.wallet.address,
                                        side=side, price=Decimal(0), size=Decimal(0))
                    cancel = self.market_instruction_builder.build_cancel_order_instructions(order)
                    cancellations += cancel

            buy_client_id = context.random_client_id()
            self.buy_client_ids += [buy_client_id]
            self.logger.info(f"Placing BUY order for {buy_size} at price {bid} with client ID: {buy_client_id}")
            buy = self.market_instruction_builder.build_place_order_instructions(
                mango.Side.BUY, mango.OrderType.POST_ONLY, bid, buy_size, buy_client_id)

            sell_client_id = context.random_client_id()
            self.sell_client_ids += [sell_client_id]
            self.logger.info(f"Placing SELL order for {sell_size} at price {ask} with client ID: {sell_client_id}")
            sell = self.market_instruction_builder.build_place_order_instructions(
                mango.Side.SELL, mango.OrderType.POST_ONLY, ask, sell_size, sell_client_id)

            settle = self.market_instruction_builder.build_settle_instructions()

            crank = self.market_instruction_builder.build_crank_instructions()
            (payer + cancellations + buy + sell + settle + crank).execute(context)
        except Exception as exception:
            self.logger.error(f"Market-maker error on pulse: {exception} - {traceback.format_exc()}")

    def __str__(self) -> str:
        return f"""« 𝙼𝚊𝚛𝚔𝚎𝚝𝙼𝚊𝚔𝚎𝚛 for market '{self.market.symbol}' »"""

    def __repr__(self) -> str:
        return f"{self}"
