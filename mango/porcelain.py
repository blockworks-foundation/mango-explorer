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

from decimal import Decimal

from .account import Account
from .context import Context
from .group import Group
from .instrumentvalue import InstrumentValue
from .loadedmarket import LoadedMarket
from .marketoperations import (
    MarketInstructionBuilder,
    MarketOperations,
    NullMarketInstructionBuilder,
    NullMarketOperations,
)
from .perpmarket import (
    PerpMarketStub,
    PerpMarket,
    PerpMarketInstructionBuilder,
    PerpMarketOperations,
)
from .serummarket import (
    SerumMarketStub,
    SerumMarket,
    SerumMarketInstructionBuilder,
    SerumMarketOperations,
)
from .spotmarket import (
    SpotMarketStub,
    SpotMarket,
    SpotMarketInstructionBuilder,
    SpotMarketOperations,
)
from .tokens import Instrument, Token
from .wallet import Wallet


# # 🥭 instrument
#
# This function takes a `Context` and an instrument symbol string (like "ETH") and returns a
# properly loaded `Instrument` object. It throws if anything goes wrong rather than return None.
#
# An Instrument can represent a Perp or an SPL token.
#
def instrument(context: Context, symbol: str) -> Instrument:
    return context.instrument(symbol)


# # 🥭 token
#
# This function takes a `Context` and a token symbol string (like "ETH") and returns a
# properly loaded `Token` object. It throws if anything goes wrong rather than return None.
#
# An Token can only represent an SPL token. It cannot represent a Perp.
#
def token(context: Context, symbol: str) -> Token:
    return context.token(symbol)


# # 🥭 instrument_value
#
# This function takes a `Context` and an instrument symbol string (like "ETH") and returns a
# properly loaded `Instrument` object. It throws if anything goes wrong rather than return None.
#
# An Instrument can represent a Perp or an SPL token.
#
def instrument_value(context: Context, symbol: str, value: Decimal) -> InstrumentValue:
    ins = context.instrument(symbol)
    return InstrumentValue(ins, value)


# # 🥭 market
#
# This function takes a `Context` and a market symbol string (like "ETH/USDC") and returns a
# properly loaded market. It throws if anything goes wrong rather than return None.
#
def market(context: Context, symbol: str) -> LoadedMarket:
    market = context.market_lookup.find_by_symbol(symbol)
    if market is None:
        raise Exception(f"Could not find market {symbol}")

    if isinstance(market, LoadedMarket):
        return market
    elif isinstance(market, SerumMarketStub):
        return market.load(context)
    elif isinstance(market, SpotMarketStub):
        group: Group = Group.load(context, market.group_address)
        return market.load(context, group)
    elif isinstance(market, PerpMarketStub):
        group = Group.load(context, market.group_address)
        return market.load(context, group)

    raise Exception(f"Market {market} could not be loaded.")


# # 🥭 instruction_builder
#
# This function deals with the creation of a `MarketInstructionBuilder` object for a given
# market.
#
def instruction_builder(
    context: Context,
    wallet: Wallet,
    account: Account,
    symbol: str,
    dry_run: bool = False,
) -> MarketInstructionBuilder:
    loaded_market: LoadedMarket = market(context, symbol)
    if dry_run:
        return NullMarketInstructionBuilder(loaded_market.fully_qualified_symbol)

    if SerumMarket.isa(loaded_market):
        return SerumMarketInstructionBuilder.load(
            context, wallet, SerumMarket.ensure(loaded_market)
        )
    elif SpotMarket.isa(loaded_market):
        spot_market = SpotMarket.ensure(loaded_market)
        return SpotMarketInstructionBuilder.load(
            context,
            wallet,
            spot_market,
            spot_market.group,
            account,
        )
    elif PerpMarket.isa(loaded_market):
        perp_market = PerpMarket.ensure(loaded_market)
        return PerpMarketInstructionBuilder.load(
            context,
            wallet,
            perp_market,
            perp_market.group,
            account,
        )

    raise Exception(f"Could not find instructions builder for market {symbol}")


# # 🥭 operations
#
# This function deals with the creation of a `MarketOperations` object for a given market.
#
def operations(
    context: Context,
    wallet: Wallet,
    account: Account,
    symbol: str,
    dry_run: bool = False,
) -> MarketOperations:
    loaded_market: LoadedMarket = market(context, symbol)
    if dry_run:
        return NullMarketOperations(loaded_market)

    if SerumMarket.isa(loaded_market):
        serum_market_instruction_builder: SerumMarketInstructionBuilder = (
            SerumMarketInstructionBuilder.load(
                context, wallet, SerumMarket.ensure(loaded_market)
            )
        )
        return SerumMarketOperations(context, wallet, serum_market_instruction_builder)
    elif SpotMarket.isa(loaded_market):
        spot_market = SpotMarket.ensure(loaded_market)
        spot_market_instruction_builder: SpotMarketInstructionBuilder = (
            SpotMarketInstructionBuilder.load(
                context, wallet, spot_market, spot_market.group, account
            )
        )
        return SpotMarketOperations(
            context, wallet, account, spot_market_instruction_builder
        )
    elif PerpMarket.isa(loaded_market):
        perp_market = PerpMarket.ensure(loaded_market)
        perp_market_instruction_builder: PerpMarketInstructionBuilder = (
            PerpMarketInstructionBuilder.load(
                context,
                wallet,
                perp_market,
                perp_market.underlying_perp_market.group,
                account,
            )
        )
        return PerpMarketOperations(
            context, wallet, account, perp_market_instruction_builder
        )

    raise Exception(f"Could not find operations for market {symbol}")
