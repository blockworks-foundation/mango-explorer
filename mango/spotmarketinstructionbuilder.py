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
from pyserum.market import Market as PySerumMarket
from solana.publickey import PublicKey

from .account import Account
from .combinableinstructions import CombinableInstructions
from .context import Context
from .group import Group
from .instructions import build_serum_consume_events_instructions, build_spot_place_order_instructions, build_cancel_spot_order_instructions, build_spot_settle_instructions, build_spot_openorders_instructions
from .marketinstructionbuilder import MarketInstructionBuilder
from .orders import Order
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
    def __init__(self, context: Context, wallet: Wallet, group: Group, account: Account, spot_market: SpotMarket, raw_market: PySerumMarket, market_index: int, fee_discount_token_address: typing.Optional[PublicKey]):
        super().__init__()
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.group: Group = group
        self.account: Account = account
        self.spot_market: SpotMarket = spot_market
        self.raw_market: PySerumMarket = raw_market
        self.market_index: int = market_index
        self.fee_discount_token_address: typing.Optional[PublicKey] = fee_discount_token_address

        self.open_orders_address: typing.Optional[PublicKey] = self.account.spot_open_orders[self.market_index]

    @staticmethod
    def load(context: Context, wallet: Wallet, group: Group, account: Account, spot_market: SpotMarket) -> "SpotMarketInstructionBuilder":
        raw_market: PySerumMarket = PySerumMarket.load(
            context.client.compatible_client, spot_market.address, context.serum_program_address)

        msrm_balance = context.client.get_token_account_balance(group.msrm_vault)
        logging.debug(f"MSRM balance is: {msrm_balance}")
        fee_discount_token_address: PublicKey = group.srm_vault
        if msrm_balance > 0:
            fee_discount_token_address = group.msrm_vault
        logging.debug(f"Using fee discount address {fee_discount_token_address}")

        market_index = group.find_spot_market_index(spot_market.address)

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

        base_rootbank = self.group.find_token_info_by_token(self.spot_market.base).root_bank
        base_nodebank = base_rootbank.pick_node_bank(self.context)
        quote_rootbank = self.group.find_token_info_by_token(self.spot_market.quote).root_bank
        quote_nodebank = quote_rootbank.pick_node_bank(self.context)
        return build_spot_settle_instructions(self.context, self.wallet, self.account,
                                              self.raw_market, self.group, self.open_orders_address,
                                              base_rootbank, base_nodebank, quote_rootbank, quote_nodebank)

    def build_crank_instructions(self, open_orders_addresses: typing.Sequence[PublicKey], limit: Decimal = Decimal(32)) -> CombinableInstructions:
        if self.open_orders_address is None:
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
        return f"« 𝚂𝚙𝚘𝚝𝙼𝚊𝚛𝚔𝚎𝚝𝙸𝚗𝚜𝚝𝚛𝚞𝚌𝚝𝚒𝚘𝚗𝙱𝚞𝚒𝚕𝚍𝚎𝚛 [{self.spot_market.symbol}] »"
