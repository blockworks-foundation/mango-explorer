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
from .ensuremarketloaded import ensure_market_loaded
from .loadedmarket import LoadedMarket


# # 🥭 load_market_by_symbol
#
# This function takes a `Context` and a market symbol string (like "ETH/USDC") and returns a loaded market. It
# throws if anything goes wrong rather than return None.
#
def load_market_by_symbol(context: Context, symbol: str) -> LoadedMarket:
    market_symbol = symbol
    market = context.market_lookup.find_by_symbol(market_symbol)
    if market is None:
        raise Exception(f"Could not find market {market_symbol}")

    return ensure_market_loaded(context, market)
