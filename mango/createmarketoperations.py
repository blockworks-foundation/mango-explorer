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


from .account import Account
from .context import Context
from .group import Group
from .market import Market
from .marketoperations import MarketOperations, NullMarketOperations
from .perpmarketinstructionbuilder import PerpMarketInstructionBuilder
from .perpmarketoperations import PerpMarketOperations
from .perpsmarket import PerpsMarket, PerpsMarketStub
from .serummarket import SerumMarket, SerumMarketStub
from .serummarketinstructionbuilder import SerumMarketInstructionBuilder
from .serummarketoperations import SerumMarketOperations
from .spotmarket import SpotMarket, SpotMarketStub
from .spotmarketinstructionbuilder import SpotMarketInstructionBuilder
from .spotmarketoperations import SpotMarketOperations
from .wallet import Wallet

# # 🥭 create_market_operations
#
# This function deals with the creation of a `MarketOperations` object for a given `Market`.


def create_market_operations(context: Context, wallet: Wallet, dry_run: bool, market: Market) -> MarketOperations:
    if dry_run:
        return NullMarketOperations(market.symbol)
    elif isinstance(market, SerumMarketStub):
        serum_market = market.load(context)
        return create_market_operations(context, wallet, dry_run, serum_market)
    elif isinstance(market, SerumMarket):
        serum_market_instruction_builder: SerumMarketInstructionBuilder = SerumMarketInstructionBuilder.load(
            context, wallet, market)
        return SerumMarketOperations(context, wallet, market, serum_market_instruction_builder)
    elif isinstance(market, SpotMarketStub):
        group: Group = Group.load(context, market.group_address)
        spot_market: SpotMarket = market.load(context, group)
        return create_market_operations(context, wallet, dry_run, spot_market)
    elif isinstance(market, SpotMarket):
        account: Account = Account.load_primary_for_owner(context, wallet.address, market.group)
        spot_market_instruction_builder: SpotMarketInstructionBuilder = SpotMarketInstructionBuilder.load(
            context, wallet, market.group, account, market)
        return SpotMarketOperations(context, wallet, market.group, account, market, spot_market_instruction_builder)
    elif isinstance(market, PerpsMarketStub):
        group = Group.load(context, market.group_address)
        perp_market: PerpsMarket = market.load(context, group)
        return create_market_operations(context, wallet, dry_run, perp_market)
    elif isinstance(market, PerpsMarket):
        account = Account.load_primary_for_owner(context, wallet.address, market.group)
        perp_market_instruction_builder: PerpMarketInstructionBuilder = PerpMarketInstructionBuilder.load(
            context, wallet, market.underlying_perp_market.group, account, market)
        return PerpMarketOperations(market.symbol, context, wallet, perp_market_instruction_builder, account, market)
    else:
        raise Exception(f"Could not find market operations handler for market {market.symbol}")
