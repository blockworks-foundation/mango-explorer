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
from solana.publickey import PublicKey

from .account import Account
from .combinableinstructions import CombinableInstructions
from .context import Context
from .group import Group
from .instructions import build_serum_consume_events_instructions, build_spot_place_order_instructions, build_cancel_spot_order_instructions, build_spot_settle_instructions
from .marketinstructionbuilder import MarketInstructionBuilder
from .orders import Order
from .spotmarket import SpotMarket
from .tokenaccount import TokenAccount
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
    def __init__(self, context: Context, wallet: Wallet, group: Group, account: Account, spot_market: SpotMarket, raw_market: Market, base_token_account: TokenAccount, quote_token_account: TokenAccount, market_index: int, fee_discount_token_address: typing.Optional[PublicKey]):
        super().__init__()
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.group: Group = group
        self.account: Account = account
        self.spot_market: SpotMarket = spot_market
        self.raw_market: Market = raw_market
        self.base_token_account: TokenAccount = base_token_account
        self.quote_token_account: TokenAccount = quote_token_account
        self.group_market_index: int = market_index
        self.fee_discount_token_address: typing.Optional[PublicKey] = fee_discount_token_address

        self.market_index = group.find_spot_market_index(spot_market.address)
        self.open_orders_address = self.account.spot_open_orders[self.market_index]

    @staticmethod
    def load(context: Context, wallet: Wallet, group: Group, account: Account, spot_market: SpotMarket) -> "SpotMarketInstructionBuilder":
        raw_market: Market = Market.load(context.client, spot_market.address, context.dex_program_id)

        fee_discount_token_address: typing.Optional[PublicKey] = None
        srm_token = context.token_lookup.find_by_symbol("SRM")
        if srm_token is not None:
            fee_discount_token_account = TokenAccount.fetch_largest_for_owner_and_token(
                context, wallet.address, srm_token)
            if fee_discount_token_account is not None:
                fee_discount_token_address = fee_discount_token_account.address

        base_token_account = TokenAccount.fetch_largest_for_owner_and_token(context, wallet.address, spot_market.base)
        if base_token_account is None:
            raise Exception(f"Could not find source token account for base token {spot_market.base.symbol}.")

        quote_token_account = TokenAccount.fetch_largest_for_owner_and_token(
            context, wallet.address, spot_market.quote)
        if quote_token_account is None:
            raise Exception(f"Could not find source token account for quote token {spot_market.quote.symbol}.")

        market_index = group.find_spot_market_index(spot_market.address)

        return SpotMarketInstructionBuilder(context, wallet, group, account, spot_market, raw_market, base_token_account, quote_token_account, market_index, fee_discount_token_address)

    def build_cancel_order_instructions(self, order: Order) -> CombinableInstructions:
        open_orders = self.account.spot_open_orders[self.group_market_index]
        return build_cancel_spot_order_instructions(
            self.context, self.wallet, self.group, self.account, self.raw_market, order, open_orders)

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
        all_open_orders_addresses: typing.List[PublicKey] = list(open_orders_addresses) + [self.open_orders_address]
        all_open_orders_addresses.sort(key=lambda address: address._key or [0])

        return build_serum_consume_events_instructions(self.context, self.spot_market.address, self.raw_market.state.event_queue(), all_open_orders_addresses, int(limit))

    def __str__(self) -> str:
        return f"« 𝚂𝚙𝚘𝚝𝙼𝚊𝚛𝚔𝚎𝚝𝙸𝚗𝚜𝚝𝚛𝚞𝚌𝚝𝚒𝚘𝚗𝙱𝚞𝚒𝚕𝚍𝚎𝚛 [{self.spot_market.symbol}] »"