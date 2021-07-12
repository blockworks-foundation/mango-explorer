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

from .desiredordersbuilder import DesiredOrdersBuilder
from .modelstate import ModelState


# # 🥭 MarketMaker class
#
# An event-driven market-maker.
#

class MarketMaker:
    def __init__(self, wallet: mango.Wallet, market: mango.Market,
                 market_instruction_builder: mango.MarketInstructionBuilder,
                 desired_orders_builder: DesiredOrdersBuilder):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.wallet: mango.Wallet = wallet
        self.market: mango.Market = market
        self.market_instruction_builder: mango.MarketInstructionBuilder = market_instruction_builder
        self.desired_orders_builder: DesiredOrdersBuilder = desired_orders_builder

        self.buy_client_ids: typing.List[int] = []
        self.sell_client_ids: typing.List[int] = []

    def pulse(self, context: mango.Context, model_state: ModelState):
        try:
            desired_orders = self.desired_orders_builder.build(context, model_state)

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

            place_orders = mango.CombinableInstructions.empty()
            for desired_order in desired_orders:
                desired_client_id: int = context.random_client_id()
                if desired_order.side == mango.Side.BUY:
                    self.buy_client_ids += [desired_client_id]
                else:
                    self.sell_client_ids += [desired_client_id]

                self.logger.info(
                    f"Placing {desired_order.side} order for {desired_order.quantity} at price {desired_order.price} with client ID: {desired_client_id}")
                place_order = self.market_instruction_builder.build_place_order_instructions(
                    desired_order.side, desired_order.order_type, desired_order.price, desired_order.quantity, desired_client_id)
                place_orders += place_order

            settle = self.market_instruction_builder.build_settle_instructions()

            crank = self.market_instruction_builder.build_crank_instructions()
            (payer + cancellations + place_orders + settle + crank).execute(context)
        except Exception as exception:
            self.logger.error(f"Market-maker error on pulse: {exception} - {traceback.format_exc()}")

    def __str__(self) -> str:
        return f"""« 𝙼𝚊𝚛𝚔𝚎𝚝𝙼𝚊𝚔𝚎𝚛 for market '{self.market.symbol}' »"""

    def __repr__(self) -> str:
        return f"{self}"
