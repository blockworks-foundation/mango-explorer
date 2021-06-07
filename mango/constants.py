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


import decimal
import json

from solana.publickey import PublicKey


# # 🥭 Constants
#
# This file contains some hard-coded values, all kept in one place, as well as the mechanism
# for loading the Mango `ids.json` file.

# ## SYSTEM_PROGRAM_ADDRESS
#
# The Solana system program address is always 11111111111111111111111111111111.


SYSTEM_PROGRAM_ADDRESS = PublicKey("11111111111111111111111111111111")


# ## SOL_MINT_ADDRESS
#
# The fake mint address of the SOL token. **Note:** Wrapped SOL has a different mint address - it is So11111111111111111111111111111111111111112.


SOL_MINT_ADDRESS = PublicKey("So11111111111111111111111111111111111111111")


# ## SOL_DECIMALS
#
# The number of decimal places used to convert Lamports into SOLs.


SOL_DECIMALS = decimal.Decimal(9)


# ## SOL_DECIMAL_DIVISOR decimal
#
# The divisor to use to turn an integer value of SOLs from an account's `balance` into a value with the correct number of decimal places.


SOL_DECIMAL_DIVISOR = decimal.Decimal(10 ** SOL_DECIMALS)


# ## NUM_TOKENS
#
# This is currently hard-coded to 3.


NUM_TOKENS = 3


# ## NUM_MARKETS
#
# There is one fewer market than tokens.


NUM_MARKETS = NUM_TOKENS - 1


# # WARNING_DISCLAIMER_TEXT
#
# This is the warning text that is output on each run of a command.


WARNING_DISCLAIMER_TEXT = """
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation
"""


# ## MangoConstants
#
# Load all Mango Market's constants from its own `ids.json` file (retrieved from [GitHub](https://raw.githubusercontent.com/blockworks-foundation/mango-client-ts/main/src/ids.json).


with open("ids.json") as json_file:
    MangoConstants = json.load(json_file)
