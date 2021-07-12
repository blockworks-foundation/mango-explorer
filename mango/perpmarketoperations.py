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
from .context import Context
from .marketoperations import MarketOperations
from .instructions import InstructionData, build_cancel_perp_order_instructions, build_place_perp_order_instructions
from .orderbookside import OrderBookSide
from .orders import Order, OrderType, Side
from .perpmarket import PerpMarket
from .wallet import Wallet


# # 🥭 PerpMarketOperations
#
# This file deals with placing orders for Perps.
#


class PerpMarketOperations(MarketOperations):
    def __init__(self, market_name: str, context: Context, wallet: Wallet,
                 margin_account: Account, perp_market: PerpMarket,
                 reporter: typing.Callable[[str], None] = None):
        super().__init__()
        self.market_name: str = market_name
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.margin_account: Account = margin_account
        self.perp_market: PerpMarket = perp_market
        self.reporter = reporter or (lambda _: None)

    def cancel_order(self, order: Order) -> str:
        report = f"Cancelling order on market {self.market_name}."
        self.logger.info(report)
        self.reporter(report)

        signers: InstructionData = InstructionData.from_wallet(self.wallet)
        cancel_instructions = build_cancel_perp_order_instructions(
            self.context, self.wallet, self.margin_account, self.perp_market, order)
        all_instructions = signers + cancel_instructions

        return all_instructions.execute_and_unwrap_transaction_id(self.context)

    def place_order(self, side: Side, order_type: OrderType, price: Decimal, size: Decimal) -> Order:
        client_order_id = self.context.random_client_id()
        report = f"Placing {order_type} {side} order for size {size} at price {price} on market {self.market_name} using client ID {client_order_id}."
        self.logger.info(report)
        self.reporter(report)

        signers: InstructionData = InstructionData.from_wallet(self.wallet)
        place_instructions = build_place_perp_order_instructions(
            self.context, self.wallet, self.perp_market.group, self.margin_account, self.perp_market, price, size, client_order_id, side, order_type)
        all_instructions = signers + place_instructions
        all_instructions.execute(self.context)

        return Order(id=0, side=side, price=price, size=size, client_id=client_order_id, owner=self.margin_account.address)

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
            if order.owner == self.margin_account.address:
                mine += [order]

        return mine

    def __str__(self) -> str:
        return f"""« 𝙿𝚎𝚛𝚙𝚜𝙾𝚛𝚍𝚎𝚛𝙿𝚕𝚊𝚌𝚎𝚛 [{self.market_name}] »"""
