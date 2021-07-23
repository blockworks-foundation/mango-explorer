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
from .perpsmarket import PerpsMarket
from .serummarket import SerumMarket
from .serummarketinstructionbuilder import SerumMarketInstructionBuilder
from .serummarketoperations import SerumMarketOperations
from .spotmarket import SpotMarket
from .spotmarketinstructionbuilder import SpotMarketInstructionBuilder
from .spotmarketoperations import SpotMarketOperations
from .wallet import Wallet

# # 🥭 create_market_operations
#
# This function deals with the creation of a `MarketOperations` object for a given `Market`.


def create_market_operations(context: Context, wallet: Wallet, dry_run: bool, market: Market) -> MarketOperations:
    if dry_run:
        return NullMarketOperations(market.symbol)
    elif isinstance(market, SerumMarket):
        serum_market_instruction_builder: SerumMarketInstructionBuilder = SerumMarketInstructionBuilder.load(
            context, wallet, market)
        return SerumMarketOperations(context, wallet, market, serum_market_instruction_builder)
    elif isinstance(market, SpotMarket):
        group = Group.load(context, market.group_address)
        accounts = Account.load_all_for_owner(context, wallet.address, group)
        account = accounts[0]
        spot_market_instruction_builder: SpotMarketInstructionBuilder = SpotMarketInstructionBuilder.load(
            context, wallet, group, account, market)
        return SpotMarketOperations(context, wallet, group, account, market, spot_market_instruction_builder)
    elif isinstance(market, PerpsMarket):
        group = Group.load(context, market.group_address)
        accounts = Account.load_all_for_owner(context, wallet.address, group)
        account = accounts[0]
        market.ensure_loaded(context)
        if market.underlying_perp_market is None:
            raise Exception(f"PerpsMarket {market.symbol} has not been loaded.")
        perp_market_instruction_builder: PerpMarketInstructionBuilder = PerpMarketInstructionBuilder.load(
            context, wallet, market.underlying_perp_market.group, account, market)

        return PerpMarketOperations(market.symbol, context, wallet, perp_market_instruction_builder, account, market)
    else:
        raise Exception(f"Could not find order placer for market {market.symbol}")
