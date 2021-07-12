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
from pyserum.market import Market

from .combinableinstructions import CombinableInstructions
from .context import Context
from .marketoperations import MarketOperations
from .orders import Order, OrderType, Side
from .serummarket import SerumMarket
from .serummarketinstructionbuilder import SerumMarketInstructionBuilder
from .wallet import Wallet


# # 🥭 SerumMarketOperations class
#
# This class puts trades on the Serum orderbook. It doesn't do anything complicated.
#

class SerumMarketOperations(MarketOperations):
    def __init__(self, context: Context, wallet: Wallet, serum_market: SerumMarket, market_instruction_builder: SerumMarketInstructionBuilder, reporter: typing.Callable[[str], None] = None):
        super().__init__()
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.serum_market: SerumMarket = serum_market
        self.market: Market = Market.load(context.client, serum_market.address, context.dex_program_id)
        self.market_instruction_builder: SerumMarketInstructionBuilder = market_instruction_builder

        def report(text):
            self.logger.info(text)
            reporter(text)

        def just_log(text):
            self.logger.info(text)

        if reporter is not None:
            self.reporter = report
        else:
            self.reporter = just_log

    def cancel_order(self, order: Order) -> typing.Sequence[str]:
        self.reporter(f"Cancelling order {order.id} on market {self.serum_market.symbol}.")
        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        cancel = self.market_instruction_builder.build_cancel_order_instructions(order)
        return (signers + cancel).execute_and_unwrap_transaction_ids(self.context)

    def place_order(self, side: Side, order_type: OrderType, price: Decimal, size: Decimal) -> Order:
        client_id: int = self.context.random_client_id()
        report: str = f"Placing {order_type} {side} order for size {size} at price {price} on market {self.serum_market.symbol} with ID {client_id}."
        self.logger.info(report)
        self.reporter(report)

        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        place = self.market_instruction_builder.build_place_order_instructions(
            side, order_type, price, size, client_id)
        (signers + place).execute(self.context)
        return Order(id=0, side=side, price=price, size=size, client_id=client_id, owner=self.market_instruction_builder.open_orders.address)

    def load_orders(self) -> typing.Sequence[Order]:
        asks = self.market.load_asks()
        orders: typing.List[Order] = []
        for serum_order in asks:
            orders += [Order.from_serum_order(serum_order)]

        bids = self.market.load_bids()
        for serum_order in bids:
            orders += [Order.from_serum_order(serum_order)]

        return orders

    def load_my_orders(self) -> typing.Sequence[Order]:
        serum_orders = self.market.load_orders_for_owner(self.wallet.address)
        orders: typing.List[Order] = []
        for serum_order in serum_orders:
            orders += [Order.from_serum_order(serum_order)]

        return orders

    def __str__(self) -> str:
        return f"""« 𝚂𝚎𝚛𝚞𝚖𝙼𝚊𝚛𝚔𝚎𝚝𝙾𝚙𝚎𝚛𝚊𝚝𝚒𝚘𝚗𝚜 [{self.serum_market.symbol}] »"""
