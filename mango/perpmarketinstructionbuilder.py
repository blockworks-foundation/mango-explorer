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
from .context import Context
from .group import Group
from .marketinstructionbuilder import MarketInstructionBuilder
from .instructions import build_cancel_perp_order_instructions, build_mango_consume_events_instructions, build_place_perp_order_instructions, build_redeem_accrued_mango_instructions
from .orders import Order
from .perpmarket import PerpMarket
from .tokeninfo import TokenInfo
from .wallet import Wallet


# # 🥭 PerpMarketInstructionBuilder
#
# This file deals with building instructions for Perp markets.
#
# As a matter of policy for all InstructionBuidlers, construction and build_* methods should all work with
# existing data, requiring no fetches from Solana or other sources. All necessary data should all be loaded
# on initial setup in the `load()` method.
#

class PerpMarketInstructionBuilder(MarketInstructionBuilder):
    def __init__(self, context: Context, wallet: Wallet, group: Group, account: Account, perp_market: PerpMarket):
        super().__init__()
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.group: Group = group
        self.account: Account = account
        self.perp_market: PerpMarket = perp_market
        self.mngo_token_info: TokenInfo = self.group.find_token_info_by_symbol("MNGO")

    @staticmethod
    def load(context: Context, wallet: Wallet, group: Group, account: Account, perp_market: PerpMarket) -> "PerpMarketInstructionBuilder":
        return PerpMarketInstructionBuilder(context, wallet, group, account, perp_market)

    def build_cancel_order_instructions(self, order: Order, ok_if_missing: bool = False) -> CombinableInstructions:
        if self.perp_market.underlying_perp_market is None:
            raise Exception(f"PerpMarket {self.perp_market.symbol} has not been loaded.")
        return build_cancel_perp_order_instructions(
            self.context, self.wallet, self.account, self.perp_market.underlying_perp_market, order, ok_if_missing)

    def build_place_order_instructions(self, order: Order) -> CombinableInstructions:
        if self.perp_market.underlying_perp_market is None:
            raise Exception(f"PerpMarket {self.perp_market.symbol} has not been loaded.")
        return build_place_perp_order_instructions(
            self.context, self.wallet, self.perp_market.underlying_perp_market.group, self.account, self.perp_market.underlying_perp_market, order.price, order.quantity, order.client_id, order.side, order.order_type)

    def build_settle_instructions(self) -> CombinableInstructions:
        return CombinableInstructions.empty()

    def build_crank_instructions(self, account_addresses: typing.Sequence[PublicKey], limit: Decimal = Decimal(32)) -> CombinableInstructions:
        if self.perp_market.underlying_perp_market is None:
            raise Exception(f"PerpMarket {self.perp_market.symbol} has not been loaded.")
        return build_mango_consume_events_instructions(self.context, self.group, self.perp_market.underlying_perp_market, account_addresses, limit)

    def build_redeem_instructions(self) -> CombinableInstructions:
        return build_redeem_accrued_mango_instructions(self.context, self.wallet, self.perp_market, self.group, self.account, self.mngo_token_info)

    def __str__(self) -> str:
        return """« 𝙿𝚎𝚛𝚙𝙼𝚊𝚛𝚔𝚎𝚝𝙸𝚗𝚜𝚝𝚛𝚞𝚌𝚝𝚒𝚘𝚗𝚜 »"""
