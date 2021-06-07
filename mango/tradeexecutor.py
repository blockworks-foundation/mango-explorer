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
import rx
import rx.operators as ops
import typing

from decimal import Decimal
from pyserum.enums import OrderType, Side
from pyserum.market import Market
from solana.account import Account
from solana.publickey import PublicKey

from .context import Context
from .openorders import OpenOrders
from .retrier import retry_context
from .spotmarket import SpotMarket, SpotMarketLookup
from .token import Token
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
    def buy(self, symbol: str, quantity: Decimal):
        raise NotImplementedError("TradeExecutor.buy() is not implemented on the base type.")

    @abc.abstractmethod
    def sell(self, symbol: str, quantity: Decimal):
        raise NotImplementedError("TradeExecutor.sell() is not implemented on the base type.")

    @abc.abstractmethod
    def settle(self, spot_market: SpotMarket, market: Market) -> typing.List[str]:
        raise NotImplementedError("TradeExecutor.settle() is not implemented on the base type.")

    @abc.abstractmethod
    def wait_for_settlement_completion(self, settlement_transaction_ids: typing.List[str]):
        raise NotImplementedError("TradeExecutor.wait_for_settlement_completion() is not implemented on the base type.")


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

    def settle(self, spot_market: SpotMarket, market: Market) -> typing.List[str]:
        self.logger.info(
            f"Skipping settling of '{spot_market.base.name}' and '{spot_market.quote.name}' in market {spot_market.address}.")
        self.reporter(
            f"Skipping settling of '{spot_market.base.name}' and '{spot_market.quote.name}' in market {spot_market.address}.")
        return []

    def wait_for_settlement_completion(self, settlement_transaction_ids: typing.List[str]):
        self.logger.info("Skipping waiting for settlement.")
        self.reporter("Skipping waiting for settlement.")


# # 🥭 SerumImmediateTradeExecutor class
#
# This class puts an IOC trade on the Serum orderbook with the expectation it will be filled
# immediately.
#
# The process the `SerumImmediateTradeExecutor` follows to place a trade is:
# * Call `place_order()` with the order details plus a random `client_id`,
# * Wait for the `client_id` to appear as a 'fill' in the market's 'event queue',
# * Call `settle_funds()` to move the trade result funds back into the wallet,
# * Wait for the `settle_funds()` transaction ID to be confirmed.
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
    def __init__(self, context: Context, wallet: Wallet, spot_market_lookup: SpotMarketLookup, price_adjustment_factor: Decimal = Decimal(0), reporter: typing.Callable[[str], None] = None):
        super().__init__()
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.spot_market_lookup: SpotMarketLookup = spot_market_lookup
        self.price_adjustment_factor: Decimal = price_adjustment_factor

        def report(text):
            self.logger.info(text)
            reporter(text)

        def just_log(text):
            self.logger.info(text)

        if reporter is not None:
            self.reporter = report
        else:
            self.reporter = just_log

    def buy(self, symbol: str, quantity: Decimal):
        spot_market = self._lookup_spot_market(symbol)
        market = Market.load(self.context.client, spot_market.address)
        self.reporter(f"BUY order market: {spot_market.address} {market}")

        asks = market.load_asks()
        top_ask = next(asks.orders())
        top_price = Decimal(top_ask.info.price)
        increase_factor = Decimal(1) + self.price_adjustment_factor
        price = top_price * increase_factor
        self.reporter(f"Price {price} - adjusted by {self.price_adjustment_factor} from {top_price}")

        source_token_account = TokenAccount.fetch_largest_for_owner_and_token(
            self.context, self.wallet.address, spot_market.quote)
        self.reporter(f"Source token account: {source_token_account}")
        if source_token_account is None:
            raise Exception(f"Could not find source token account for '{spot_market.quote}'")

        self._execute(
            spot_market,
            market,
            Side.BUY,
            source_token_account,
            spot_market.base,
            spot_market.quote,
            price,
            quantity
        )

    def sell(self, symbol: str, quantity: Decimal):
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

        source_token_account = TokenAccount.fetch_largest_for_owner_and_token(
            self.context, self.wallet.address, spot_market.base)
        self.reporter(f"Source token account: {source_token_account}")
        if source_token_account is None:
            raise Exception(f"Could not find source token account for '{spot_market.base}'")

        self._execute(
            spot_market,
            market,
            Side.SELL,
            source_token_account,
            spot_market.base,
            spot_market.quote,
            price,
            quantity
        )

    def _execute(self, spot_market: SpotMarket, market: Market, side: Side, source_token_account: TokenAccount, base_token: Token, quote_token: Token, price: Decimal, quantity: Decimal):
        with retry_context("Serum Place Order", self._place_order, self.context.retry_pauses) as retrier:
            client_id, place_order_transaction_id = retrier.run(
                market, base_token, quote_token, source_token_account.address, self.wallet.account, OrderType.IOC, side, price, quantity)

        with retry_context("Serum Wait For Order Fill", self._wait_for_order_fill, self.context.retry_pauses) as retrier:
            retrier.run(market, client_id)

        with retry_context("Serum Settle", self.settle, self.context.retry_pauses) as retrier:
            settlement_transaction_ids = retrier.run(spot_market, market)

        with retry_context("Serum Wait For Settle Completion", self.wait_for_settlement_completion, self.context.retry_pauses) as retrier:
            retrier.run(settlement_transaction_ids)

        self.reporter("Order execution complete")

    def _place_order(self, market: Market, base_token: Token, quote_token: Token, paying_token_address: PublicKey, account: Account, order_type: OrderType, side: Side, price: Decimal, quantity: Decimal) -> typing.Tuple[int, str]:
        to_pay = price * quantity
        self.logger.info(
            f"{side.name}ing {quantity} of {base_token.name} at {price} for {to_pay} on {base_token.name}/{quote_token.name} from {paying_token_address}.")

        client_id = self.context.random_client_id()
        self.reporter(f"""Placing order
    paying_token_address: {paying_token_address}
    account: {account.public_key()}
    order_type: {order_type.name}
    side: {side.name}
    price: {float(price)}
    quantity: {float(quantity)}
    client_id: {client_id}""")

        response = market.place_order(paying_token_address, account, order_type,
                                      side, float(price), float(quantity), client_id)
        transaction_id = self.context.unwrap_transaction_id_or_raise_exception(response)
        self.reporter(f"Order transaction ID: {transaction_id}")

        return client_id, transaction_id

    def _wait_for_order_fill(self, market: Market, client_id: int, max_wait_in_seconds: int = 60):
        self.logger.info(f"Waiting up to {max_wait_in_seconds} seconds for {client_id}.")
        return rx.interval(1.0).pipe(
            ops.flat_map(lambda _: market.load_event_queue()),
            ops.skip_while(lambda item: item.client_order_id != client_id),
            ops.skip_while(lambda item: not item.event_flags.fill),
            ops.first(),
            ops.map(lambda _: True),
            ops.timeout(max_wait_in_seconds, rx.return_value(False))
        ).run()

    def settle(self, spot_market: SpotMarket, market: Market) -> typing.List[str]:
        base_token_account = TokenAccount.fetch_or_create_largest_for_owner_and_token(
            self.context, self.wallet.account, spot_market.base)
        quote_token_account = TokenAccount.fetch_or_create_largest_for_owner_and_token(
            self.context, self.wallet.account, spot_market.quote)

        open_orders = OpenOrders.load_for_market_and_owner(self.context, spot_market.address, self.wallet.account.public_key(
        ), self.context.dex_program_id, spot_market.base.decimals, spot_market.quote.decimals)

        transaction_ids = []
        for open_order_account in open_orders:
            if (open_order_account.base_token_free > 0) or (open_order_account.quote_token_free > 0):
                self.reporter(
                    f"Need to settle open orders: {open_order_account}\nBase account: {base_token_account.address}\nQuote account: {quote_token_account.address}")
                response = market.settle_funds(self.wallet.account, open_order_account.to_pyserum(
                ), base_token_account.address, quote_token_account.address)
                transaction_id = self.context.unwrap_transaction_id_or_raise_exception(response)
                self.reporter(f"Settlement transaction ID: {transaction_id}")
                transaction_ids += [transaction_id]

        return transaction_ids

    def wait_for_settlement_completion(self, settlement_transaction_ids: typing.List[str]):
        if len(settlement_transaction_ids) > 0:
            self.reporter(f"Waiting on settlement transaction IDs: {settlement_transaction_ids}")
            for settlement_transaction_id in settlement_transaction_ids:
                self.reporter(f"Waiting on specific settlement transaction ID: {settlement_transaction_id}")
                self.context.wait_for_confirmation(settlement_transaction_id)
            self.reporter("All settlement transaction IDs confirmed.")

    def _lookup_spot_market(self, symbol: str) -> SpotMarket:
        spot_market = self.spot_market_lookup.find_by_symbol(symbol)
        if spot_market is None:
            raise Exception(f"Spot market '{symbol}' could not be found.")

        self.logger.info(f"Base token: {spot_market.base}")
        self.logger.info(f"Quote token: {spot_market.quote}")

        return spot_market

    def __str__(self) -> str:
        return f"""« SerumImmediateTradeExecutor [{self.price_adjustment_factor}] »"""

    def __repr__(self) -> str:
        return f"{self}"
