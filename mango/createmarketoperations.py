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

from .account import Account
from .context import Context
from .ensuremarketloaded import ensure_market_loaded
from .loadedmarket import LoadedMarket
from .market import Market
from .marketoperations import (
    MarketInstructionBuilder,
    MarketOperations,
    NullMarketInstructionBuilder,
    NullMarketOperations,
)
from .perpmarket import PerpMarket
from .perpmarketoperations import PerpMarketInstructionBuilder, PerpMarketOperations
from .serummarket import SerumMarket
from .serummarketoperations import SerumMarketInstructionBuilder, SerumMarketOperations
from .spotmarket import SpotMarket
from .spotmarketoperations import SpotMarketInstructionBuilder, SpotMarketOperations
from .wallet import Wallet


# # 🥭 create_market_instruction_builder
#
# This function deals with the creation of a `MarketInstructionBuilder` object for a given `Market`.
#
def create_market_instruction_builder(
    context: Context,
    wallet: Wallet,
    account: Account,
    market: Market,
    dry_run: bool = False,
) -> MarketInstructionBuilder:
    if dry_run:
        return NullMarketInstructionBuilder(market.symbol)

    loaded_market: Market = ensure_market_loaded(context, market)
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
    else:
        raise Exception(
            f"Could not find market instructions builder for market {market.symbol}"
        )


# # 🥭 create_market_operations
#
# This function deals with the creation of a `MarketOperations` object for a given `Market`.
#
def create_market_operations(
    context: Context,
    wallet: Wallet,
    account: typing.Optional[Account],
    market: Market,
    dry_run: bool = False,
) -> MarketOperations:
    loaded_market: LoadedMarket = ensure_market_loaded(context, market)

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
        if account is None:
            raise Exception("Account is required for SpotMarket operations.")
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
        if account is None:
            raise Exception("Account is required for PerpMarket operations.")
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
    else:
        raise Exception(
            f"Could not find market operations handler for market {market.symbol}"
        )
