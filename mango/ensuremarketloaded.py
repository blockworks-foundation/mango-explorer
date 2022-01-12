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


from .context import Context
from .group import Group
from .loadedmarket import LoadedMarket
from .market import Market
from .perpmarket import PerpMarketStub
from .serummarket import SerumMarketStub
from .spotmarket import SpotMarketStub


# # 🥭 ensure_market_loaded function
#
# This function ensures that a `Market` is 'loaded' and not a 'stub'. Stubs are handy for laoding in
# bulk, for instance in a market lookup, but real processing usually requires a fully loaded `Market`.
#
# This function simplifies turning a stub into a fully-loaded, usable market.
#
def ensure_market_loaded(context: Context, market: Market) -> LoadedMarket:
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


# # 🥭 load_market_by_symbol
#
# This function takes a `Context` and a market symbol string (like "ETH/USDC") and returns a loaded market. It
# throws if anything goes wrong rather than return None.
#
def load_market_by_symbol(context: Context, symbol: str) -> LoadedMarket:
    market = context.market_lookup.find_by_symbol(symbol)
    if market is None:
        raise Exception(f"Could not find market {symbol}")

    return ensure_market_loaded(context, market)
