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


import abc
import logging
import typing

import spl.token.instructions as spl_token

from decimal import Decimal
from pyserum.enums import OrderType, Side
from pyserum.market import Market
from solana.account import Account
from solana.publickey import PublicKey
from solana.transaction import Transaction

from .context import Context
from .instructions import ConsumeEventsInstructionBuilder, CreateSerumOpenOrdersInstructionBuilder, NewOrderV3InstructionBuilder, SettleInstructionBuilder
from .retrier import retry_context
from .spotmarket import SpotMarket
from .tokenaccount import TokenAccount
from .wallet import Wallet


# # 🥭 TradeExecutor
#
# This file deals with executing trades. We want the interface to be as simple as:
# ```
# trade_executor.buy("ETH", 2.5)
# ```
# but this (necessarily) masks a great deal of complexity. The aim is to keep the complexity
# around trades within these `TradeExecutor` classes.
#

# # 🥭 TradeExecutor class
#
# This abstracts the process of placing trades, based on our typed objects.
#
# It's abstracted because we may want to have different approaches to executing these
# trades - do we want to run them against the Serum orderbook? Would it be faster if we
# ran them against Raydium?
#
# Whichever choice is made, the calling code shouldn't have to care. It should be able to
# use its `TradeExecutor` class as simply as:
# ```
# trade_executor.buy("ETH", 2.5)
# ```
#

class TradeExecutor(metaclass=abc.ABCMeta):
    def __init__(self):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def buy(self, symbol: str, quantity: Decimal) -> str:
        raise NotImplementedError("TradeExecutor.buy() is not implemented on the base type.")

    @abc.abstractmethod
    def sell(self, symbol: str, quantity: Decimal) -> str:
        raise NotImplementedError("TradeExecutor.sell() is not implemented on the base type.")


# # 🥭 NullTradeExecutor class
#
# A null, no-op, dry-run trade executor that can be plugged in anywhere a `TradeExecutor`
# is expected, but which will not actually trade.
#

class NullTradeExecutor(TradeExecutor):
    def __init__(self, reporter: typing.Callable[[str], None] = None):
        super().__init__()
        self.reporter = reporter or (lambda _: None)

    def buy(self, symbol: str, quantity: Decimal):
        self.logger.info(f"Skipping BUY trade of {quantity:,.8f} of '{symbol}'.")
        self.reporter(f"Skipping BUY trade of {quantity:,.8f} of '{symbol}'.")

    def sell(self, symbol: str, quantity: Decimal):
        self.logger.info(f"Skipping SELL trade of {quantity:,.8f} of '{symbol}'.")
        self.reporter(f"Skipping SELL trade of {quantity:,.8f} of '{symbol}'.")


# # 🥭 SerumImmediateTradeExecutor class
#
# This class puts an IOC trade on the Serum orderbook with the expectation it will be filled
# immediately. It follows the pattern described here:
#   https://solanadev.blogspot.com/2021/05/order-techniques-with-project-serum.html
#
# Here's an example (Raydium?) transaction that does this:
#   https://solanabeach.io/transaction/3Hb2h7QMM3BbJCK42BUDuVEYwwaiqfp2oQUZMDJvUuoyCRJD5oBmA3B8oAGkB9McdCFtwdT2VrSKM2GCKhJ92FpY
#
# Basically, it tries to send to a 'market buy/sell' and settle all in one transaction.
#
# It does this by:
# * Sending a Place Order (V3) instruction
# * Sending a Consume Events (crank) instruction
# * Sending a Settle Funds instruction
# all in the same transaction. With V3 Serum, this should work (assuming the IOC order
# is filled).
#
# It also creates the Serum OpenOrders account for the transaction if it doesn't
# already exist.
#
# The SerumImmediateTradeExecutor constructor takes a `price_adjustment_factor` to allow
# moving the price it is willing to pay away from the mid-price. Testing shows the price is
# filled at the orderbook price if the price we specify is worse, so it looks like it's
# possible to be quite liberal with this adjustment. In a live test:
# * Original wallet USDT value was 342.8606.
# * `price_adjustment_factor` was 0.05.
# * ETH price was 2935.14 USDT (on 2021-05-02).
# * Adjusted price was 3081.897 USDT, adjusted by 1.05 from 2935.14
# * Buying 0.1 ETH specifying 3081.897 as the price resulted in:
#   * Buying 0.1 ETH
#   * Spending 294.1597 USDT
# * After settling, the wallet should hold 342.8606 USDT - 294.1597 USDT = 48.7009 USDT
# * The wallet did indeed hold 48.7009 USDT
#
# So: the specified BUY price of 3081.897 USDT was taken as a maximum, and orders were taken
# from the orderbook starting at the current cheapest, until the order was filled or (I'm
# assuming) the price exceeded the price specified.
#


class SerumImmediateTradeExecutor(TradeExecutor):
    def __init__(self, context: Context, wallet: Wallet, price_adjustment_factor: Decimal = Decimal(0), reporter: typing.Callable[[str], None] = None):
        super().__init__()
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.price_adjustment_factor: Decimal = price_adjustment_factor
        self._serum_fee_discount_token_address: typing.Optional[PublicKey] = None
        self._serum_fee_discount_token_address_loaded: bool = False

        def report(text):
            self.logger.info(text)
            reporter(text)

        def just_log(text):
            self.logger.info(text)

        if reporter is not None:
            self.reporter = report
        else:
            self.reporter = just_log

    @property
    def serum_fee_discount_token_address(self) -> typing.Optional[PublicKey]:
        if self._serum_fee_discount_token_address_loaded:
            return self._serum_fee_discount_token_address

        # SRM is always the token Serum uses for fee discounts
        token = self.context.token_lookup.find_by_symbol("SRM")
        if token is None:
            raise Exception("Could not load token details for SRM")

        fee_discount_token_account = TokenAccount.fetch_largest_for_owner_and_token(
            self.context, self.wallet.address, token)
        if fee_discount_token_account is not None:
            self._serum_fee_discount_token_address = fee_discount_token_account.address

        self._serum_fee_discount_token_address_loaded = True
        return self._serum_fee_discount_token_address

    def buy(self, symbol: str, quantity: Decimal) -> str:
        spot_market = self._lookup_spot_market(symbol)
        market = Market.load(self.context.client, spot_market.address)
        self.reporter(f"BUY order market: {spot_market.address} {market}")

        asks = market.load_asks()
        top_ask = next(asks.orders())
        top_price = Decimal(top_ask.info.price)
        increase_factor = Decimal(1) + self.price_adjustment_factor
        price = top_price * increase_factor
        self.reporter(f"Price {price} - adjusted by {self.price_adjustment_factor} from {top_price}")

        return self._execute(
            spot_market,
            market,
            Side.BUY,
            price,
            quantity
        )

    def sell(self, symbol: str, quantity: Decimal) -> str:
        spot_market = self._lookup_spot_market(symbol)
        market = Market.load(self.context.client, spot_market.address)
        self.reporter(f"SELL order market: {spot_market.address} {market}")

        bids = market.load_bids()
        bid_orders = list(bids.orders())
        top_bid = bid_orders[len(bid_orders) - 1]
        top_price = Decimal(top_bid.info.price)
        decrease_factor = Decimal(1) - self.price_adjustment_factor
        price = top_price * decrease_factor
        self.reporter(f"Price {price} - adjusted by {self.price_adjustment_factor} from {top_price}")

        return self._execute(
            spot_market,
            market,
            Side.SELL,
            price,
            quantity
        )

    def _execute(self, spot_market: SpotMarket, market: Market, side: Side, price: Decimal, quantity: Decimal) -> str:
        transaction = Transaction()
        signers: typing.List[Account] = [self.wallet.account]

        base_token_account = TokenAccount.fetch_largest_for_owner_and_token(
            self.context, self.wallet.address, spot_market.base)
        if base_token_account is None:
            create_base_token_account = spl_token.create_associated_token_account(
                payer=self.wallet.address, owner=self.wallet.address, mint=spot_market.base.mint
            )
            transaction.add(create_base_token_account)
            base_token_account_address = create_base_token_account.keys[1].pubkey
        else:
            base_token_account_address = base_token_account.address

        quote_token_account = TokenAccount.fetch_largest_for_owner_and_token(
            self.context, self.wallet.address, spot_market.quote)
        if quote_token_account is None:
            create_quote_token_account = spl_token.create_associated_token_account(
                payer=self.wallet.address, owner=self.wallet.address, mint=spot_market.quote.mint
            )
            transaction.add(create_quote_token_account)
            quote_token_account_address = create_quote_token_account.keys[1].pubkey
        else:
            quote_token_account_address = quote_token_account.address

        if side == Side.BUY:
            source_token_account_address = quote_token_account_address
        else:
            source_token_account_address = base_token_account_address

        open_order_accounts = market.find_open_orders_accounts_for_owner(self.wallet.address)
        if not open_order_accounts:
            new_open_orders_account = Account()
            create_open_orders = CreateSerumOpenOrdersInstructionBuilder(
                self.context, self.wallet, market, new_open_orders_account.public_key())
            transaction.add(create_open_orders.build())
            signers.append(new_open_orders_account)
            open_orders_address: PublicKey = new_open_orders_account.public_key()
            open_orders_addresses: typing.List[PublicKey] = [open_orders_address]
        else:
            open_orders_address = open_order_accounts[0].address
            open_orders_addresses = list(oo.address for oo in open_order_accounts)

        client_id = self.context.random_client_id()
        new_order = NewOrderV3InstructionBuilder(self.context, self.wallet, market,
                                                 source_token_account_address,
                                                 open_orders_address, OrderType.IOC,
                                                 side, price, quantity, client_id,
                                                 self.serum_fee_discount_token_address)
        transaction.add(new_order.build())

        consume_events = ConsumeEventsInstructionBuilder(self.context, self.wallet, market, open_orders_addresses)
        transaction.add(consume_events.build())

        settle = SettleInstructionBuilder(self.context, self.wallet, market,
                                          open_orders_address, base_token_account_address, quote_token_account_address)
        transaction.add(settle.build())

        with retry_context("Place Serum Order And Settle", self.context.client.send_transaction, self.context.retry_pauses) as retrier:
            response = retrier.run(transaction, *signers, opts=self.context.transaction_options)
            return self.context.unwrap_transaction_id_or_raise_exception(response)

    def _lookup_spot_market(self, symbol: str) -> SpotMarket:
        spot_market = self.context.market_lookup.find_by_symbol(symbol)
        if spot_market is None:
            raise Exception(f"Spot market '{symbol}' could not be found.")

        if not isinstance(spot_market, SpotMarket):
            raise Exception(f"Spot market '{symbol}' is not a Serum market.")

        self.logger.info(f"Base token: {spot_market.base}")
        self.logger.info(f"Quote token: {spot_market.quote}")

        return spot_market

    def __str__(self) -> str:
        return f"""« SerumImmediateTradeExecutor [{self.price_adjustment_factor}] »"""

    def __repr__(self) -> str:
        return f"{self}"
