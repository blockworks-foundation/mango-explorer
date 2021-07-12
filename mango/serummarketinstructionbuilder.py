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


import pyserum.enums
import typing

from decimal import Decimal
from pyserum.market import Market
from solana.publickey import PublicKey

from .combinableinstructions import CombinableInstructions
from .context import Context
from .marketinstructionbuilder import MarketInstructionBuilder
from .openorders import OpenOrders
from .orders import Order, OrderType, Side
from .serummarket import SerumMarket
from .tokenaccount import TokenAccount
from .wallet import Wallet


# # 🥭 SerumMarketInstructionBuilder
#
# This file deals with building instructions for Serum markets.
#
# As a matter of policy for all InstructionBuidlers, construction and build_* methods should all work with
# existing data, requiring no fetches from Solana or other sources. All necessary data should all be loaded
# on initial setup in the `load()` method.
#

class SerumMarketInstructionBuilder(MarketInstructionBuilder):
    def __init__(self, context: Context, wallet: Wallet, serum_market: SerumMarket, raw_market: Market, base_token_account: TokenAccount, quote_token_account: TokenAccount, open_orders: OpenOrders, fee_discount_token_address: typing.Optional[PublicKey]):
        super().__init__()
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.serum_market: SerumMarket = serum_market
        self.raw_market: Market = raw_market
        self.base_token_account: TokenAccount = base_token_account
        self.quote_token_account: TokenAccount = quote_token_account
        self.open_orders: OpenOrders = open_orders
        self.fee_discount_token_address: typing.Optional[PublicKey] = fee_discount_token_address

    @staticmethod
    def load(context: Context, wallet: Wallet, serum_market: SerumMarket) -> "SerumMarketInstructionBuilder":
        raw_market: Market = Market.load(context.client, serum_market.address, context.dex_program_id)

        fee_discount_token_address: typing.Optional[PublicKey] = None
        srm_token = context.token_lookup.find_by_symbol("SRM")
        if srm_token is not None:
            fee_discount_token_account = TokenAccount.fetch_largest_for_owner_and_token(
                context, wallet.address, srm_token)
            if fee_discount_token_account is not None:
                fee_discount_token_address = fee_discount_token_account.address

        all_open_orders = OpenOrders.load_for_market_and_owner(
            context, serum_market.address, wallet.address, context.dex_program_id, serum_market.base.decimals, serum_market.quote.decimals)
        if len(all_open_orders) == 0:
            raise Exception(f"No OpenOrders account available for market {serum_market}.")
        open_orders = all_open_orders[0]

        base_token_account = TokenAccount.fetch_largest_for_owner_and_token(context, wallet.address, serum_market.base)
        if base_token_account is None:
            raise Exception(f"Could not find source token account for base token {serum_market.base.symbol}.")

        quote_token_account = TokenAccount.fetch_largest_for_owner_and_token(
            context, wallet.address, serum_market.quote)
        if quote_token_account is None:
            raise Exception(f"Could not find source token account for quote token {serum_market.quote.symbol}.")

        return SerumMarketInstructionBuilder(context, wallet, serum_market, raw_market, base_token_account, quote_token_account, open_orders, fee_discount_token_address)

    def build_cancel_order_instructions(self, order: Order) -> CombinableInstructions:
        instruction = self.raw_market.make_cancel_order_by_client_id_instruction(
            self, self.wallet.account, self.open_orders.address, order.client_id
        )
        return CombinableInstructions.from_instruction(instruction)

    def build_place_order_instructions(self, side: Side, order_type: OrderType, price: Decimal, size: Decimal, client_id: int) -> CombinableInstructions:
        serum_order_type = pyserum.enums.OrderType.POST_ONLY if order_type == OrderType.POST_ONLY else pyserum.enums.OrderType.IOC if order_type == OrderType.IOC else pyserum.enums.OrderType.LIMIT
        serum_side = pyserum.enums.Side.BUY if side == Side.BUY else pyserum.enums.Side.SELL
        payer_token_account = self.quote_token_account if side == Side.BUY else self.base_token_account

        instruction = self.raw_market.make_place_order_instruction(payer_token_account.address, self.wallet.account, serum_order_type, serum_side, float(
            price), float(size), client_id, self.open_orders.address, self.fee_discount_token_address)

        return CombinableInstructions.from_instruction(instruction)

    def build_settle_instructions(self) -> CombinableInstructions:
        return CombinableInstructions.empty()

    def build_crank_instructions(self, limit: Decimal = Decimal(32)) -> CombinableInstructions:
        return CombinableInstructions.empty()

    def __str__(self) -> str:
        return """« 𝚂𝚎𝚛𝚞𝚖𝙼𝚊𝚛𝚔𝚎𝚝𝙸𝚗𝚜𝚝𝚛𝚞𝚌𝚝𝚒𝚘𝚗𝙱𝚞𝚒𝚕𝚍𝚎𝚛 »"""
