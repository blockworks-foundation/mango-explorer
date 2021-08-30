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

from decimal import Decimal
from solana.publickey import PublicKey

from .account import Account
from .context import Context
from .createmarketoperations import create_market_operations
from .marketoperations import MarketOperations
from .orders import Order, OrderType, Side
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
    def buy(self, symbol: str, quantity: Decimal) -> Order:
        raise NotImplementedError("TradeExecutor.buy() is not implemented on the base type.")

    @abc.abstractmethod
    def sell(self, symbol: str, quantity: Decimal) -> Order:
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

    def buy(self, symbol: str, quantity: Decimal) -> Order:
        self.logger.info(f"Skipping BUY trade of {quantity:,.8f} of '{symbol}'.")
        self.reporter(f"Skipping BUY trade of {quantity:,.8f} of '{symbol}'.")
        return Order.from_basic_info(Side.BUY, Decimal(0), quantity)

    def sell(self, symbol: str, quantity: Decimal) -> Order:
        self.logger.info(f"Skipping SELL trade of {quantity:,.8f} of '{symbol}'.")
        self.reporter(f"Skipping SELL trade of {quantity:,.8f} of '{symbol}'.")
        return Order.from_basic_info(Side.SELL, Decimal(0), quantity)


# # 🥭 ImmediateTradeExecutor class
#
# This class puts an IOC trade on the orderbook with the expectation it will be filled
# immediately. It follows the pattern described here:
#   https://solanadev.blogspot.com/2021/05/order-techniques-with-project-serum.html
#
# Basically, it tries to send a 'market buy/sell' and settle all in one transaction.
#
# The ImmediateTradeExecutor constructor takes a `price_adjustment_factor` to allow
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
class ImmediateTradeExecutor(TradeExecutor):
    def __init__(self, context: Context, wallet: Wallet, account: typing.Optional[Account], price_adjustment_factor: Decimal = Decimal(0), reporter: typing.Callable[[str], None] = None):
        super().__init__()
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.account: typing.Optional[Account] = account
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

    def buy(self, symbol: str, quantity: Decimal) -> Order:
        market_operations: MarketOperations = self._build_market_operations(symbol)
        orders = market_operations.load_orders()

        top_ask = min([order.price for order in orders if order.side == Side.SELL])

        increase_factor = Decimal(1) + self.price_adjustment_factor
        price = top_ask * increase_factor
        self.reporter(f"Price {price} - adjusted by {self.price_adjustment_factor} from {top_ask}")

        order = Order.from_basic_info(Side.BUY, price, quantity, OrderType.IOC)
        return market_operations.place_order(order)

    def sell(self, symbol: str, quantity: Decimal) -> Order:
        market_operations: MarketOperations = self._build_market_operations(symbol)
        orders = market_operations.load_orders()

        top_bid = max([order.price for order in orders if order.side == Side.BUY])

        decrease_factor = Decimal(1) - self.price_adjustment_factor
        price = top_bid * decrease_factor
        self.reporter(f"Price {price} - adjusted by {self.price_adjustment_factor} from {top_bid}")

        order = Order.from_basic_info(Side.SELL, price, quantity, OrderType.IOC)
        return market_operations.place_order(order)

    def _build_market_operations(self, symbol: str) -> MarketOperations:
        market = self.context.market_lookup.find_by_symbol(symbol)
        if market is None:
            raise Exception(f"Market '{symbol}' could not be found.")

        return create_market_operations(self.context, self.wallet, self.account, market)

    def __str__(self) -> str:
        return f"""« 𝙸𝚖𝚖𝚎𝚍𝚒𝚊𝚝𝚎𝚃𝚛𝚊𝚍𝚎𝙴𝚡𝚎𝚌𝚞𝚝𝚘𝚛 [{self.price_adjustment_factor}] »"""

    def __repr__(self) -> str:
        return f"{self}"
