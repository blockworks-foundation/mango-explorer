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

from .account import Account
from .combinableinstructions import CombinableInstructions
from .context import Context
from .marketoperations import MarketOperations
from .orders import Order, OrderType, Side
from .perpmarketinstructionbuilder import PerpMarketInstructionBuilder
from .perpsmarket import PerpsMarket
from .wallet import Wallet


# # 🥭 PerpMarketOperations
#
# This file deals with placing orders for Perps.
#


class PerpMarketOperations(MarketOperations):
    def __init__(self, market_name: str, context: Context, wallet: Wallet,
                 market_instruction_builder: PerpMarketInstructionBuilder,
                 account: Account, perps_market: PerpsMarket):
        super().__init__()
        self.market_name: str = market_name
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.market_instruction_builder: PerpMarketInstructionBuilder = market_instruction_builder
        self.account: Account = account
        self.perps_market: PerpsMarket = perps_market

    def cancel_order(self, order: Order) -> typing.Sequence[str]:
        self.logger.info(f"Cancelling {self.market_name} order {order}.")
        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        cancel: CombinableInstructions = self.market_instruction_builder.build_cancel_order_instructions(order)
        accounts_to_crank = self.perps_market.accounts_to_crank(self.context, self.account.address)
        crank = self.market_instruction_builder.build_crank_instructions(accounts_to_crank)
        return (signers + cancel + crank).execute_and_unwrap_transaction_ids(self.context)

    def place_order(self, side: Side, order_type: OrderType, price: Decimal, quantity: Decimal) -> Order:
        client_id: int = self.context.random_client_id()
        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        order: Order = Order(id=0, client_id=client_id, owner=self.account.address,
                             side=side, price=price, quantity=quantity, order_type=order_type)
        self.logger.info(f"Placing {self.market_name} order {order}.")
        place: CombinableInstructions = self.market_instruction_builder.build_place_order_instructions(order)
        accounts_to_crank = self.perps_market.accounts_to_crank(self.context, self.account.address)
        crank = self.market_instruction_builder.build_crank_instructions(accounts_to_crank)
        (signers + place + crank).execute(self.context)
        return order

    def settle(self) -> typing.Sequence[str]:
        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        settle = self.market_instruction_builder.build_settle_instructions()
        return (signers + settle).execute(self.context)

    def crank(self, limit: Decimal = Decimal(32)) -> typing.Sequence[str]:
        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        accounts_to_crank = self.perps_market.accounts_to_crank(self.context, self.account.address)
        crank = self.market_instruction_builder.build_crank_instructions(accounts_to_crank, limit)
        return (signers + crank).execute(self.context)

    def load_orders(self) -> typing.Sequence[Order]:
        return self.perps_market.orders(self.context)

    def load_my_orders(self) -> typing.Sequence[Order]:
        orders = self.load_orders()
        mine = []
        for order in orders:
            if order.owner == self.account.address:
                mine += [order]

        return mine

    def __str__(self) -> str:
        return f"""« 𝙿𝚎𝚛𝚙𝚜𝙾𝚛𝚍𝚎𝚛𝙿𝚕𝚊𝚌𝚎𝚛 [{self.market_name}] »"""
