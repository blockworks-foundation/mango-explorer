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

from .combinableinstructions import CombinableInstructions
from .constants import SYSTEM_PROGRAM_ADDRESS
from .context import Context
from .marketoperations import MarketOperations
from .orders import Order
from .serummarket import SerumMarket
from .serummarketinstructionbuilder import SerumMarketInstructionBuilder
from .wallet import Wallet


# # 🥭 SerumMarketOperations class
#
# This class performs standard operations on the Serum orderbook.
#
class SerumMarketOperations(MarketOperations):
    def __init__(self, context: Context, wallet: Wallet, serum_market: SerumMarket, market_instruction_builder: SerumMarketInstructionBuilder):
        super().__init__(serum_market)
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.serum_market: SerumMarket = serum_market
        self.market_instruction_builder: SerumMarketInstructionBuilder = market_instruction_builder

    def cancel_order(self, order: Order, ok_if_missing: bool = False) -> typing.Sequence[str]:
        self.logger.info(f"Cancelling {self.serum_market.symbol} order {order}.")
        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        cancel: CombinableInstructions = self.market_instruction_builder.build_cancel_order_instructions(
            order, ok_if_missing=ok_if_missing)
        crank: CombinableInstructions = self._build_crank()
        settle: CombinableInstructions = self.market_instruction_builder.build_settle_instructions()
        return (signers + cancel + crank + settle).execute(self.context)

    def place_order(self, order: Order) -> Order:
        client_id: int = self.context.generate_client_id()
        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        open_orders_address = self.market_instruction_builder.open_orders_address or SYSTEM_PROGRAM_ADDRESS
        order_with_client_id: Order = Order(id=0, client_id=client_id, side=order.side, price=order.price,
                                            quantity=order.quantity, owner=open_orders_address,
                                            order_type=order.order_type)
        self.logger.info(f"Placing {self.serum_market.symbol} order {order_with_client_id}.")
        place: CombinableInstructions = self.market_instruction_builder.build_place_order_instructions(
            order_with_client_id)

        crank: CombinableInstructions = self._build_crank()
        settle: CombinableInstructions = self.market_instruction_builder.build_settle_instructions()

        (signers + place + crank + settle).execute(self.context)
        return order

    def settle(self) -> typing.Sequence[str]:
        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        settle = self.market_instruction_builder.build_settle_instructions()
        return (signers + settle).execute(self.context)

    def crank(self, limit: Decimal = Decimal(32)) -> typing.Sequence[str]:
        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        crank = self._build_crank(limit)
        return (signers + crank).execute(self.context)

    def create_openorders(self) -> PublicKey:
        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        create_open_orders = self.market_instruction_builder.build_create_openorders_instructions()
        open_orders_address = create_open_orders.signers[0].public_key
        (signers + create_open_orders).execute(self.context)

        return open_orders_address

    def ensure_openorders(self) -> PublicKey:
        if self.market_instruction_builder.open_orders_address is not None:
            return self.market_instruction_builder.open_orders_address
        return self.create_openorders()

    def load_orders(self) -> typing.Sequence[Order]:
        return self.serum_market.orders(self.context)

    def load_my_orders(self) -> typing.Sequence[Order]:
        open_orders_address = self.market_instruction_builder.open_orders_address
        if not open_orders_address:
            return []

        all_orders = self.serum_market.orders(self.context)
        return list([o for o in all_orders if o.owner == open_orders_address])

    def _build_crank(self, limit: Decimal = Decimal(32)) -> CombinableInstructions:
        open_orders_to_crank: typing.List[PublicKey] = []
        for event in self.serum_market.unprocessed_events(self.context):
            open_orders_to_crank += [event.public_key]

        if len(open_orders_to_crank) == 0:
            return CombinableInstructions.empty()

        return self.market_instruction_builder.build_crank_instructions(open_orders_to_crank, limit)

    def __str__(self) -> str:
        return f"""« 𝚂𝚎𝚛𝚞𝚖𝙼𝚊𝚛𝚔𝚎𝚝𝙾𝚙𝚎𝚛𝚊𝚝𝚒𝚘𝚗𝚜 [{self.serum_market.symbol}] »"""
