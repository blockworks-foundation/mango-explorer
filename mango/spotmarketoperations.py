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
from .combinableinstructions import CombinableInstructions
from .constants import SYSTEM_PROGRAM_ADDRESS
from .context import Context
from .group import Group
from .marketoperations import MarketOperations
from .orders import Order
from .spotmarket import SpotMarket
from .spotmarketinstructionbuilder import SpotMarketInstructionBuilder
from .wallet import Wallet


# # 🥭 SpotMarketOperations class
#
# This class puts trades on the Serum orderbook. It doesn't do anything complicated.
#
class SpotMarketOperations(MarketOperations):
    def __init__(self, context: Context, wallet: Wallet, group: Group, account: Account, spot_market: SpotMarket, market_instruction_builder: SpotMarketInstructionBuilder):
        super().__init__(spot_market)
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.group: Group = group
        self.account: Account = account
        self.spot_market: SpotMarket = spot_market
        self.market_instruction_builder: SpotMarketInstructionBuilder = market_instruction_builder

        self.market_index: int = group.find_spot_market_index(spot_market.address)
        self.open_orders_address: typing.Optional[PublicKey] = self.account.spot_open_orders[self.market_index]

    def cancel_order(self, order: Order, ok_if_missing: bool = False) -> typing.Sequence[str]:
        self.logger.info(f"Cancelling {self.spot_market.symbol} order {order}.")
        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        cancel: CombinableInstructions = self.market_instruction_builder.build_cancel_order_instructions(
            order, ok_if_missing=ok_if_missing)
        crank: CombinableInstructions = self._build_crank(add_self=True)
        settle: CombinableInstructions = self.market_instruction_builder.build_settle_instructions()

        return (signers + cancel + crank + settle).execute(self.context)

    def place_order(self, order: Order) -> Order:
        client_id: int = self.context.generate_client_id()
        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        order_with_client_id: Order = order.with_client_id(client_id).with_owner(
            self.open_orders_address or SYSTEM_PROGRAM_ADDRESS)
        self.logger.info(f"Placing {self.spot_market.symbol} order {order}.")
        place: CombinableInstructions = self.market_instruction_builder.build_place_order_instructions(
            order_with_client_id)
        crank: CombinableInstructions = self._build_crank(add_self=True)
        settle: CombinableInstructions = self.market_instruction_builder.build_settle_instructions()

        transaction_ids = (signers + place + crank + settle).execute(self.context)
        self.logger.info(f"Transaction IDs: {transaction_ids}.")

        return order_with_client_id

    def settle(self) -> typing.Sequence[str]:
        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        settle = self.market_instruction_builder.build_settle_instructions()
        return (signers + settle).execute(self.context)

    def crank(self, limit: Decimal = Decimal(32)) -> typing.Sequence[str]:
        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        crank = self._build_crank(limit, add_self=False)
        return (signers + crank).execute(self.context)

    def create_openorders(self) -> PublicKey:
        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        create_open_orders: CombinableInstructions = self.market_instruction_builder.build_create_openorders_instructions()
        open_orders_address: PublicKey = create_open_orders.signers[0].public_key
        (signers + create_open_orders).execute(self.context)

        # This line is a little nasty. Now that we know we have an OpenOrders account at this address, update
        # the Account so that future uses (like later in this method) have access to it in the right place.
        self.account.update_spot_open_orders_for_market(self.market_index, open_orders_address)

        return open_orders_address

    def ensure_openorders(self) -> PublicKey:
        existing: typing.Optional[PublicKey] = self.account.spot_open_orders[self.market_index]
        if existing is not None:
            return existing
        return self.create_openorders()

    def load_orders(self) -> typing.Sequence[Order]:
        return self.spot_market.orders(self.context)

    def load_my_orders(self) -> typing.Sequence[Order]:
        if not self.open_orders_address:
            return []

        all_orders = self.spot_market.orders(self.context)
        return list([o for o in all_orders if o.owner == self.open_orders_address])

    def _build_crank(self, limit: Decimal = Decimal(32), add_self: bool = False) -> CombinableInstructions:
        open_orders_to_crank: typing.List[PublicKey] = []
        for event in self.spot_market.unprocessed_events(self.context):
            open_orders_to_crank += [event.public_key]

        if add_self and self.open_orders_address is not None:
            open_orders_to_crank += [self.open_orders_address]

        if len(open_orders_to_crank) == 0:
            return CombinableInstructions.empty()

        return self.market_instruction_builder.build_crank_instructions(open_orders_to_crank, limit)

    def __str__(self) -> str:
        return f"""« 𝚂𝚙𝚘𝚝𝙼𝚊𝚛𝚔𝚎𝚝𝙾𝚙𝚎𝚛𝚊𝚝𝚒𝚘𝚗𝚜 [{self.spot_market.symbol}] »"""
