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

from .oracle import OracleProvider
from .oracles.ftx import ftx
from .oracles.pythnetwork import pythnetwork
from .oracles.serum import serum
from .spotmarket import SpotMarketLookup


# # 🥭 Oracle Factory
#
# This file allows you to create a concreate OracleProvider for a specified provider name.
#

def create_oracle_provider(provider_name: str, spot_market_lookup: SpotMarketLookup) -> OracleProvider:
    if provider_name == "serum":
        return serum.SerumOracleProvider(spot_market_lookup)
    elif provider_name == "ftx":
        return ftx.FtxOracleProvider()
    elif provider_name == "pyth":
        return pythnetwork.PythOracleProvider()
    raise Exception(f"Unknown oracle provider '{provider_name}'.")
