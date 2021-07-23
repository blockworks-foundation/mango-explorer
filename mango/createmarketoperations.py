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
from .ensuremarketloaded import ensure_market_loaded
from .market import Market
from .marketoperations import MarketOperations, NullMarketOperations
from .perpmarketinstructionbuilder import PerpMarketInstructionBuilder
from .perpmarketoperations import PerpMarketOperations
from .perpmarket import PerpMarket
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

    loaded_market: Market = ensure_market_loaded(context, market)
    if isinstance(loaded_market, SerumMarket):
        serum_market_instruction_builder: SerumMarketInstructionBuilder = SerumMarketInstructionBuilder.load(
            context, wallet, loaded_market)
        return SerumMarketOperations(context, wallet, loaded_market, serum_market_instruction_builder)
    elif isinstance(loaded_market, SpotMarket):
        account: Account = Account.load_primary_for_owner(context, wallet.address, loaded_market.group)
        spot_market_instruction_builder: SpotMarketInstructionBuilder = SpotMarketInstructionBuilder.load(
            context, wallet, loaded_market.group, account, loaded_market)
        return SpotMarketOperations(context, wallet, loaded_market.group, account, loaded_market, spot_market_instruction_builder)
    elif isinstance(loaded_market, PerpMarket):
        account = Account.load_primary_for_owner(context, wallet.address, loaded_market.group)
        perp_market_instruction_builder: PerpMarketInstructionBuilder = PerpMarketInstructionBuilder.load(
            context, wallet, loaded_market.underlying_perp_market.group, account, loaded_market)
        return PerpMarketOperations(loaded_market.symbol, context, wallet, perp_market_instruction_builder, account, loaded_market)
    else:
        raise Exception(f"Could not find market operations handler for market {market.symbol}")
