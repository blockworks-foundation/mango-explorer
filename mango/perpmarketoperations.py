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
from solana.publickey import PublicKey

from .account import Account
from .accountinfo import AccountInfo
from .combinableinstructions import CombinableInstructions
from .context import Context
from .marketoperations import MarketOperations
from .orderbookside import OrderBookSide
from .orders import Order, OrderType, Side
from .perpmarket import PerpMarket
from .perpmarketinstructionbuilder import PerpMarketInstructionBuilder
from .wallet import Wallet


# # 🥭 PerpMarketOperations
#
# This file deals with placing orders for Perps.
#


class PerpMarketOperations(MarketOperations):
    def __init__(self, market_name: str, context: Context, wallet: Wallet,
                 market_instruction_builder: PerpMarketInstructionBuilder,
                 account: Account, perp_market: PerpMarket):
        super().__init__()
        self.market_name: str = market_name
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.market_instruction_builder: PerpMarketInstructionBuilder = market_instruction_builder
        self.account: Account = account
        self.perp_market: PerpMarket = perp_market

    def cancel_order(self, order: Order) -> typing.Sequence[str]:
        self.logger.info(
            f"Cancelling order {order.id} for quantity {order.quantity} at price {order.price} on market {self.market_name} with client ID {order.client_id}.")
        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        cancel = self.market_instruction_builder.build_cancel_order_instructions(order)
        return (signers + cancel).execute_and_unwrap_transaction_ids(self.context)

    def place_order(self, side: Side, order_type: OrderType, price: Decimal, quantity: Decimal) -> Order:
        client_id: int = self.context.random_client_id()
        self.logger.info(
            f"Placing {order_type} {side} order for quantity {quantity} at price {price} on market {self.market_name} with ID {client_id}.")

        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        order = Order(id=0, client_id=client_id, owner=self.account.address,
                      side=side, price=price, quantity=quantity, order_type=order_type)
        place = self.market_instruction_builder.build_place_order_instructions(order)
        (signers + place).execute(self.context)
        return order

    def load_orders(self) -> typing.Sequence[Order]:
        bids_address: PublicKey = self.perp_market.bids
        asks_address: PublicKey = self.perp_market.asks
        [bids, asks] = AccountInfo.load_multiple(self.context, [bids_address, asks_address])
        bid_side = OrderBookSide.parse(self.context, bids, self.perp_market)
        ask_side = OrderBookSide.parse(self.context, asks, self.perp_market)

        return [*bid_side.orders(), *ask_side.orders()]

    def load_my_orders(self) -> typing.Sequence[Order]:
        orders = self.load_orders()
        mine = []
        for order in orders:
            if order.owner == self.account.address:
                mine += [order]

        return mine

    def __str__(self) -> str:
        return f"""« 𝙿𝚎𝚛𝚙𝚜𝙾𝚛𝚍𝚎𝚛𝙿𝚕𝚊𝚌𝚎𝚛 [{self.market_name}] »"""
