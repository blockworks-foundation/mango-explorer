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
import typing

from decimal import Decimal
from pyserum.market.market import Market as PySerumMarket
from solana.publickey import PublicKey

from .account import Account
from .combinableinstructions import CombinableInstructions
from .constants import SYSTEM_PROGRAM_ADDRESS
from .context import Context
from .group import GroupSlot, Group
from .instructions import build_serum_consume_events_instructions, build_spot_place_order_instructions, build_cancel_spot_order_instructions, build_spot_settle_instructions, build_spot_openorders_instructions
from .marketoperations import MarketInstructionBuilder, MarketOperations
from .orders import Order, OrderBook
from .publickey import encode_public_key_for_sorting
from .spotmarket import SpotMarket
from .wallet import Wallet


# # 🥭 SpotMarketInstructionBuilder
#
# This file deals with building instructions for Spot markets.
#
# As a matter of policy for all InstructionBuidlers, construction and build_* methods should all work with
# existing data, requiring no fetches from Solana or other sources. All necessary data should all be loaded
# on initial setup in the `load()` method.
#
class SpotMarketInstructionBuilder(MarketInstructionBuilder):
    def __init__(self, context: Context, wallet: Wallet, group: Group, account: Account,
                 spot_market: SpotMarket, raw_market: PySerumMarket, market_index: int,
                 fee_discount_token_address: PublicKey) -> None:
        super().__init__()
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.group: Group = group
        self.account: Account = account
        self.spot_market: SpotMarket = spot_market
        self.raw_market: PySerumMarket = raw_market
        self.market_index: int = market_index
        self.fee_discount_token_address: PublicKey = fee_discount_token_address

        self.open_orders_address: typing.Optional[PublicKey] = self.account.spot_open_orders_by_index[self.market_index]

    @staticmethod
    def load(context: Context, wallet: Wallet, group: Group, account: Account, spot_market: SpotMarket) -> "SpotMarketInstructionBuilder":
        raw_market: PySerumMarket = PySerumMarket.load(
            context.client.compatible_client, spot_market.address, context.serum_program_address)

        msrm_balance = context.client.get_token_account_balance(group.msrm_vault)
        fee_discount_token_address: PublicKey
        if msrm_balance > 0:
            fee_discount_token_address = group.msrm_vault
            logging.debug(
                f"MSRM balance is: {msrm_balance} - using MSRM fee discount address {fee_discount_token_address}")
        else:
            fee_discount_token_address = group.srm_vault
            logging.debug(
                f"MSRM balance is: {msrm_balance} - using SRM fee discount address {fee_discount_token_address}")

        slot = group.slot_by_spot_market_address(spot_market.address)
        market_index = slot.index

        return SpotMarketInstructionBuilder(context, wallet, group, account, spot_market, raw_market, market_index, fee_discount_token_address)

    def build_cancel_order_instructions(self, order: Order, ok_if_missing: bool = False) -> CombinableInstructions:
        if self.open_orders_address is None:
            return CombinableInstructions.empty()

        return build_cancel_spot_order_instructions(
            self.context, self.wallet, self.group, self.account, self.raw_market, order, self.open_orders_address)

    def build_place_order_instructions(self, order: Order) -> CombinableInstructions:
        return build_spot_place_order_instructions(self.context, self.wallet, self.group, self.account,
                                                   self.raw_market, order.order_type, order.side, order.price,
                                                   order.quantity, order.client_id,
                                                   self.fee_discount_token_address)

    def build_settle_instructions(self) -> CombinableInstructions:
        if self.open_orders_address is None:
            return CombinableInstructions.empty()

        base_slot: GroupSlot = self.group.slot_by_instrument(self.spot_market.base)
        if base_slot.base_token_bank is None:
            raise Exception(
                f"No token info for base instrument {self.spot_market.base.symbol} in group {self.group.address}")
        base_rootbank = base_slot.base_token_bank.ensure_root_bank(self.context)
        base_nodebank = base_rootbank.pick_node_bank(self.context)

        quote_rootbank = self.group.shared_quote.ensure_root_bank(self.context)
        quote_nodebank = quote_rootbank.pick_node_bank(self.context)
        return build_spot_settle_instructions(self.context, self.wallet, self.account,
                                              self.raw_market, self.group, self.open_orders_address,
                                              base_rootbank, base_nodebank, quote_rootbank, quote_nodebank)

    def build_crank_instructions(self, open_orders_addresses: typing.Sequence[PublicKey], limit: Decimal = Decimal(32)) -> CombinableInstructions:
        if self.open_orders_address is None:
            self._logger.debug("Returning empty crank instructions - no spot OpenOrders address provided.")
            return CombinableInstructions.empty()

        open_orders_to_crank: typing.Sequence[PublicKey] = [*open_orders_addresses, self.open_orders_address]
        distinct_open_orders_addresses: typing.List[PublicKey] = []
        for oo in open_orders_to_crank:
            if oo not in distinct_open_orders_addresses:
                distinct_open_orders_addresses += [oo]

        limited_open_orders_addresses = distinct_open_orders_addresses[0:min(
            int(limit), len(distinct_open_orders_addresses))]

        limited_open_orders_addresses.sort(key=encode_public_key_for_sorting)

        return build_serum_consume_events_instructions(self.context, self.spot_market.address, self.raw_market.state.event_queue(), limited_open_orders_addresses, int(limit))

    def build_redeem_instructions(self) -> CombinableInstructions:
        return CombinableInstructions.empty()

    def build_create_openorders_instructions(self) -> CombinableInstructions:
        return build_spot_openorders_instructions(self.context, self.wallet, self.group, self.account, self.raw_market)

    def __str__(self) -> str:
        return f"« SpotMarketInstructionBuilder [{self.spot_market.symbol}] »"


# # 🥭 SpotMarketOperations class
#
# This class puts trades on the Serum orderbook. It doesn't do anything complicated.
#
class SpotMarketOperations(MarketOperations):
    def __init__(self, context: Context, wallet: Wallet, group: Group, account: Account,
                 spot_market: SpotMarket, market_instruction_builder: SpotMarketInstructionBuilder) -> None:
        super().__init__(spot_market)
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.group: Group = group
        self.account: Account = account
        self.spot_market: SpotMarket = spot_market
        self.market_instruction_builder: SpotMarketInstructionBuilder = market_instruction_builder

        self.market_index: int = group.slot_by_spot_market_address(spot_market.address).index
        self.open_orders_address: typing.Optional[PublicKey] = self.account.spot_open_orders_by_index[self.market_index]

    def cancel_order(self, order: Order, ok_if_missing: bool = False) -> typing.Sequence[str]:
        self._logger.info(f"Cancelling {self.spot_market.symbol} order {order}.")
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
        self._logger.info(f"Placing {self.spot_market.symbol} order {order}.")
        place: CombinableInstructions = self.market_instruction_builder.build_place_order_instructions(
            order_with_client_id)
        crank: CombinableInstructions = self._build_crank(add_self=True)
        settle: CombinableInstructions = self.market_instruction_builder.build_settle_instructions()

        transaction_ids = (signers + place + crank + settle).execute(self.context)
        self._logger.info(f"Transaction IDs: {transaction_ids}.")

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
        existing: typing.Optional[PublicKey] = self.account.spot_open_orders_by_index[self.market_index]
        if existing is not None:
            return existing
        return self.create_openorders()

    def load_orderbook(self) -> OrderBook:
        return self.spot_market.fetch_orderbook(self.context)

    def load_my_orders(self) -> typing.Sequence[Order]:
        if not self.open_orders_address:
            return []

        orderbook: OrderBook = self.load_orderbook()
        return list([o for o in [*orderbook.bids, *orderbook.asks] if o.owner == self.open_orders_address])

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
        return f"« SpotMarketOperations [{self.spot_market.symbol}] »"
