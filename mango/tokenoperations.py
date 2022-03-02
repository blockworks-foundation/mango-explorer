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

from decimal import Decimal

from solana.publickey import PublicKey

from .accountinfo import AccountInfo
from .combinableinstructions import CombinableInstructions
from .context import Context
from .instructions import build_spl_create_associated_account_instructions
from .instrumentvalue import InstrumentValue
from .tokenaccount import TokenAccount
from .tokens import Token
from .version import Version
from .wallet import Wallet


def build_create_associated_instructions_and_account(
    context: Context, wallet: Wallet, owner: PublicKey, token: Token
) -> typing.Tuple[CombinableInstructions, TokenAccount]:
    create_ata = build_spl_create_associated_account_instructions(
        context, wallet, owner, token
    )
    ata_address = TokenAccount.derive_associated_token_address(owner, token)
    account_info = AccountInfo(
        ata_address, False, Decimal(0), owner, Decimal(0), bytes()
    )
    token_account = TokenAccount(
        account_info,
        Version.UNSPECIFIED,
        owner,
        InstrumentValue(token, Decimal(0)),
    )

    return create_ata, token_account
