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
from pyserum.market import Market as PySerumMarket
from solana.publickey import PublicKey

from .combinableinstructions import CombinableInstructions
from .context import Context
from .instructions import build_create_serum_open_orders_instructions, build_serum_consume_events_instructions, build_serum_settle_instructions
from .marketinstructionbuilder import MarketInstructionBuilder
from .openorders import OpenOrders
from .orders import Order, Side
from .publickey import encode_public_key_for_sorting
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
    def __init__(self, context: Context, wallet: Wallet, serum_market: SerumMarket, raw_market: PySerumMarket, base_token_account: TokenAccount, quote_token_account: TokenAccount, open_orders_address: typing.Optional[PublicKey], fee_discount_token_address: typing.Optional[PublicKey]):
        super().__init__()
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.serum_market: SerumMarket = serum_market
        self.raw_market: PySerumMarket = raw_market
        self.base_token_account: TokenAccount = base_token_account
        self.quote_token_account: TokenAccount = quote_token_account
        self.open_orders_address: typing.Optional[PublicKey] = open_orders_address
        self.fee_discount_token_address: typing.Optional[PublicKey] = fee_discount_token_address

    @staticmethod
    def load(context: Context, wallet: Wallet, serum_market: SerumMarket) -> "SerumMarketInstructionBuilder":
        raw_market: PySerumMarket = PySerumMarket.load(
            context.client.compatible_client, serum_market.address, context.serum_program_address)

        fee_discount_token_address: typing.Optional[PublicKey] = None
        srm_token = context.token_lookup.find_by_symbol("SRM")
        if srm_token is not None:
            fee_discount_token_account = TokenAccount.fetch_largest_for_owner_and_token(
                context, wallet.address, srm_token)
            if fee_discount_token_account is not None:
                fee_discount_token_address = fee_discount_token_account.address

        open_orders_address: typing.Optional[PublicKey] = None
        all_open_orders = OpenOrders.load_for_market_and_owner(
            context, serum_market.address, wallet.address, context.serum_program_address, serum_market.base.decimals, serum_market.quote.decimals)
        if len(all_open_orders) > 0:
            open_orders_address = all_open_orders[0].address

        base_token_account = TokenAccount.fetch_largest_for_owner_and_token(context, wallet.address, serum_market.base)
        if base_token_account is None:
            raise Exception(f"Could not find source token account for base token {serum_market.base.symbol}.")

        quote_token_account = TokenAccount.fetch_largest_for_owner_and_token(
            context, wallet.address, serum_market.quote)
        if quote_token_account is None:
            raise Exception(f"Could not find source token account for quote token {serum_market.quote.symbol}.")

        return SerumMarketInstructionBuilder(context, wallet, serum_market, raw_market, base_token_account, quote_token_account, open_orders_address, fee_discount_token_address)

    def build_cancel_order_instructions(self, order: Order, ok_if_missing: bool = False) -> CombinableInstructions:
        # For us to cancel an order, an open_orders account must already exist (or have existed).
        if self.open_orders_address is None:
            raise Exception(f"Cannot cancel order with client ID {order.client_id} - no OpenOrders account.")

        raw_instruction = self.raw_market.make_cancel_order_by_client_id_instruction(
            self.wallet.to_deprecated_solana_account(), self.open_orders_address, order.client_id
        )
        return CombinableInstructions.from_instruction(raw_instruction)

    def build_place_order_instructions(self, order: Order) -> CombinableInstructions:
        ensure_open_orders = CombinableInstructions.empty()
        if self.open_orders_address is None:
            ensure_open_orders = self.build_create_openorders_instructions()

        if self.open_orders_address is None:
            raise Exception("Failed to find or create OpenOrders address")

        serum_order_type: pyserum.enums.OrderType = order.order_type.to_serum()
        serum_side: pyserum.enums.Side = order.side.to_serum()
        payer_token_account = self.quote_token_account if order.side == Side.BUY else self.base_token_account

        raw_instruction = self.raw_market.make_place_order_instruction(payer_token_account.address,
                                                                       self.wallet.to_deprecated_solana_account(),
                                                                       serum_order_type,
                                                                       serum_side,
                                                                       float(order.price),
                                                                       float(order.quantity),
                                                                       order.client_id,
                                                                       self.open_orders_address,
                                                                       self.fee_discount_token_address)

        place = CombinableInstructions.from_instruction(raw_instruction)

        return ensure_open_orders + place

    def build_settle_instructions(self) -> CombinableInstructions:
        if self.open_orders_address is None:
            return CombinableInstructions.empty()
        return build_serum_settle_instructions(self.context, self.wallet, self.raw_market, self.open_orders_address, self.base_token_account.address, self.quote_token_account.address)

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

        return build_serum_consume_events_instructions(self.context, self.serum_market.address, self.raw_market.state.event_queue(), limited_open_orders_addresses, int(limit))

    def build_create_openorders_instructions(self) -> CombinableInstructions:
        create_open_orders = build_create_serum_open_orders_instructions(self.context, self.wallet, self.raw_market)
        self.open_orders_address = create_open_orders.signers[0].public_key
        return create_open_orders

    def build_redeem_instructions(self) -> CombinableInstructions:
        return CombinableInstructions.empty()

    def __str__(self) -> str:
        return """« 𝚂𝚎𝚛𝚞𝚖𝙼𝚊𝚛𝚔𝚎𝚝𝙸𝚗𝚜𝚝𝚛𝚞𝚌𝚝𝚒𝚘𝚗𝙱𝚞𝚒𝚕𝚍𝚎𝚛 »"""
