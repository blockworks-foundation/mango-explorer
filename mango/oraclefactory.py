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
from .oracle import OracleProvider
from .oracles.ftx import ftx
from .oracles.pythnetwork import pythnetwork
from .oracles.serum import serum
from .oracles.stub import stub


# # 🥭 Oracle Factory
#
# This file allows you to create a concreate OracleProvider for a specified provider name.
#

def create_oracle_provider(context: Context, provider_name: str) -> OracleProvider:
    if provider_name == "serum":
        return serum.SerumOracleProvider()
    elif provider_name == "ftx":
        return ftx.FtxOracleProvider()
    elif provider_name == "pyth":
        return pythnetwork.PythOracleProvider(context)
    elif provider_name == "pyth-mainnet":
        mainnet_beta_pyth_context: Context = context.new_forced_to_mainnet_beta()
        return pythnetwork.PythOracleProvider(mainnet_beta_pyth_context)
    elif provider_name == "pyth-devnet":
        devnet_pyth_context: Context = context.new_forced_to_devnet()
        return pythnetwork.PythOracleProvider(devnet_pyth_context)
    elif provider_name == "stub":
        return stub.StubOracleProvider()
    raise Exception(f"Unknown oracle provider '{provider_name}'.")
