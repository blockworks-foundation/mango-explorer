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
from .marketinstructionbuilder import MarketInstructionBuilder, NullMarketInstructionBuilder
from .perpmarketinstructionbuilder import PerpMarketInstructionBuilder
from .perpmarket import PerpMarket
from .serummarket import SerumMarket
from .serummarketinstructionbuilder import SerumMarketInstructionBuilder
from .spotmarket import SpotMarket
from .spotmarketinstructionbuilder import SpotMarketInstructionBuilder
from .wallet import Wallet

# # 🥭 create_market_instruction_builder
#
# This function deals with the creation of a `MarketInstructionBuilder` object for a given `Market`.


def create_market_instruction_builder(context: Context, wallet: Wallet, account: Account, market: Market, dry_run: bool = False) -> MarketInstructionBuilder:
    if dry_run:
        return NullMarketInstructionBuilder(market.symbol)

    loaded_market: Market = ensure_market_loaded(context, market)
    if isinstance(loaded_market, SerumMarket):
        return SerumMarketInstructionBuilder.load(context, wallet, loaded_market)
    elif isinstance(loaded_market, SpotMarket):
        return SpotMarketInstructionBuilder.load(context, wallet, loaded_market.group, account, loaded_market)
    elif isinstance(loaded_market, PerpMarket):
        return PerpMarketInstructionBuilder.load(
            context, wallet, loaded_market.group, account, loaded_market)
    else:
        raise Exception(f"Could not find market instructions builder for market {market.symbol}")
