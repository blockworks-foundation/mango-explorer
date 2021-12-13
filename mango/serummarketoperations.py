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
from pyserum.market.market import Market as PySerumMarket
from solana.publickey import PublicKey

from .combinableinstructions import CombinableInstructions
from .constants import SYSTEM_PROGRAM_ADDRESS
from .context import Context
from .instructions import build_create_serum_open_orders_instructions, build_serum_consume_events_instructions, build_serum_settle_instructions, build_serum_place_order_instructions
from .marketoperations import MarketInstructionBuilder, MarketOperations
from .openorders import OpenOrders
from .orders import Order, OrderBook, Side
from .publickey import encode_public_key_for_sorting
from .serummarket import SerumMarket
from .token import Instrument, Token
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
    def __init__(self, context: Context, wallet: Wallet, serum_market: SerumMarket, raw_market: PySerumMarket,
                 base_token_account: TokenAccount, quote_token_account: TokenAccount,
                 open_orders_address: typing.Optional[PublicKey],
                 fee_discount_token_address: PublicKey) -> None:
        super().__init__()
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.serum_market: SerumMarket = serum_market
        self.raw_market: PySerumMarket = raw_market
        self.base_token_account: TokenAccount = base_token_account
        self.quote_token_account: TokenAccount = quote_token_account
        self.open_orders_address: typing.Optional[PublicKey] = open_orders_address
        self.fee_discount_token_address: PublicKey = fee_discount_token_address

    @staticmethod
    def load(context: Context, wallet: Wallet, serum_market: SerumMarket) -> "SerumMarketInstructionBuilder":
        raw_market: PySerumMarket = PySerumMarket.load(
            context.client.compatible_client, serum_market.address, context.serum_program_address)

        fee_discount_token_address: PublicKey = SYSTEM_PROGRAM_ADDRESS
        srm_instrument: typing.Optional[Instrument] = context.instrument_lookup.find_by_symbol("SRM")
        if srm_instrument is not None:
            srm_token: Token = Token.ensure(srm_instrument)
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
            self.wallet.keypair, self.open_orders_address, order.client_id
        )
        return CombinableInstructions.from_instruction(raw_instruction)

    def build_place_order_instructions(self, order: Order) -> CombinableInstructions:
        ensure_open_orders = CombinableInstructions.empty()
        if self.open_orders_address is None:
            ensure_open_orders = self.build_create_openorders_instructions()

        if self.open_orders_address is None:
            raise Exception("Failed to find or create OpenOrders address")

        payer_token_account = self.quote_token_account if order.side == Side.BUY else self.base_token_account
        place = build_serum_place_order_instructions(self.context, self.wallet, self.raw_market,
                                                     payer_token_account.address, self.open_orders_address,
                                                     order.order_type, order.side, order.price,
                                                     order.quantity, order.client_id,
                                                     self.fee_discount_token_address)

        return ensure_open_orders + place

    def build_settle_instructions(self) -> CombinableInstructions:
        if self.open_orders_address is None:
            return CombinableInstructions.empty()
        return build_serum_settle_instructions(self.context, self.wallet, self.raw_market, self.open_orders_address, self.base_token_account.address, self.quote_token_account.address)

    def build_crank_instructions(self, open_orders_addresses: typing.Sequence[PublicKey], limit: Decimal = Decimal(32)) -> CombinableInstructions:
        if self.open_orders_address is None:
            self._logger.debug("Returning empty crank instructions - no serum OpenOrders address provided.")
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
        return """« SerumMarketInstructionBuilder »"""


# # 🥭 SerumMarketOperations class
#
# This class performs standard operations on the Serum orderbook.
#
class SerumMarketOperations(MarketOperations):
    def __init__(self, context: Context, wallet: Wallet, serum_market: SerumMarket,
                 market_instruction_builder: SerumMarketInstructionBuilder) -> None:
        super().__init__(serum_market)
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.serum_market: SerumMarket = serum_market
        self.market_instruction_builder: SerumMarketInstructionBuilder = market_instruction_builder

    def cancel_order(self, order: Order, ok_if_missing: bool = False) -> typing.Sequence[str]:
        self._logger.info(f"Cancelling {self.serum_market.symbol} order {order}.")
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
        self._logger.info(f"Placing {self.serum_market.symbol} order {order_with_client_id}.")
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

    def load_orderbook(self) -> OrderBook:
        return self.serum_market.fetch_orderbook(self.context)

    def load_my_orders(self) -> typing.Sequence[Order]:
        open_orders_address = self.market_instruction_builder.open_orders_address
        if not open_orders_address:
            return []

        orderbook: OrderBook = self.load_orderbook()
        return list([o for o in [*orderbook.bids, *orderbook.asks] if o.owner == open_orders_address])

    def _build_crank(self, limit: Decimal = Decimal(32)) -> CombinableInstructions:
        open_orders_to_crank: typing.List[PublicKey] = []
        for event in self.serum_market.unprocessed_events(self.context):
            open_orders_to_crank += [event.public_key]

        if len(open_orders_to_crank) == 0:
            return CombinableInstructions.empty()

        return self.market_instruction_builder.build_crank_instructions(open_orders_to_crank, limit)

    def __str__(self) -> str:
        return f"""« SerumMarketOperations [{self.serum_market.symbol}] »"""
