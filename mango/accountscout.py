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

from solana.publickey import PublicKey

from .account import Account
from .accountinfo import AccountInfo
from .constants import SYSTEM_PROGRAM_ADDRESS
from .context import Context
from .group import Group
from .token import Token
from .tokenaccount import TokenAccount
from .wallet import Wallet


# # 🥭 AccountScout
#
# Required Accounts
#
# Mango Markets code expects some accounts to be present, and if they're not present some
# actions can fail.
#
# From [Daffy on Discord](https://discord.com/channels/791995070613159966/820390560085835786/834024719958147073):
#
# > You need an open orders account for each of the spot markets Mango. And you need a
# token account for each of the tokens.
#
# This notebook (and the `AccountScout` class) can be used to check the required accounts
# are present and maybe in future set up all the required accounts.
#
# (There's no reason not to write the code to fix problems and create any missing accounts.
# It just hasn't been done yet.)
#


# # 🥭 ScoutReport class
#
# The `ScoutReport` class is built up by the `AccountScout` to report errors, warnings and
# details pertaining to a user account.
#


class ScoutReport:
    def __init__(self, address: PublicKey):
        self.address = address
        self.errors: typing.List[str] = []
        self.warnings: typing.List[str] = []
        self.details: typing.List[str] = []

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def add_error(self, error: str) -> None:
        self.errors += [error]

    def add_warning(self, warning: str) -> None:
        self.warnings += [warning]

    def add_detail(self, detail: str) -> None:
        self.details += [detail]

    def __str__(self) -> str:
        def _pad(text_list: typing.List[str]) -> str:
            if len(text_list) == 0:
                return "None"
            padding = "\n        "
            return padding.join(map(lambda text: text.replace("\n", padding), text_list))

        error_text = _pad(self.errors)
        warning_text = _pad(self.warnings)
        detail_text = _pad(self.details)
        if len(self.errors) > 0 or len(self.warnings) > 0:
            summary = f"Found {len(self.errors)} error(s) and {len(self.warnings)} warning(s)."
        else:
            summary = "No problems found"

        return f"""« ScoutReport [{self.address}]:
    Summary:
        {summary}

    Errors:
        {error_text}

    Warnings:
        {warning_text}

    Details:
        {detail_text}
»"""

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 AccountScout class
#
# The `AccountScout` class aims to run various checks against a user account to make sure
# it is in a position to run the liquidator.
#
# Passing all checks here with no errors will be a precondition on liquidator startup.
#

class AccountScout:
    def __init__(self) -> None:
        pass

    def require_account_prepared_for_group(self, context: Context, group: Group, account_address: PublicKey) -> None:
        report = self.verify_account_prepared_for_group(context, group, account_address)
        if report.has_errors:
            raise Exception(f"Account '{account_address}' is not prepared for group '{group.address}':\n\n{report}")

    def verify_account_prepared_for_group(self, context: Context, group: Group, account_address: PublicKey) -> ScoutReport:
        report = ScoutReport(account_address)

        # First of all, the account must actually exist. If it doesn't, just return early.
        root_account = AccountInfo.load(context, account_address)
        if root_account is None:
            report.add_error(f"Root account '{account_address}' does not exist.")
            return report

        # For this to be a user/wallet account, it must be owned by 11111111111111111111111111111111.
        if root_account.owner != SYSTEM_PROGRAM_ADDRESS:
            report.add_error(f"Account '{account_address}' is not a root user account.")
            return report

        # Must have token accounts for each of the tokens in the group's basket.
        for basket_token in group.tokens:
            if isinstance(basket_token.token, Token):
                token_accounts = TokenAccount.fetch_all_for_owner_and_token(
                    context, account_address, basket_token.token)
                if len(token_accounts) == 0:
                    report.add_error(
                        f"Account '{account_address}' has no account for token '{basket_token.token.name}'.")
                else:
                    report.add_detail(
                        f"Account '{account_address}' has {len(token_accounts)} {basket_token.token.name} token account(s): {[ta.address for ta in token_accounts]}")

        # May have one or more Mango Markets margin account, but it's optional for liquidating
        accounts = Account.load_all_for_owner(context, account_address, group)
        if len(accounts) == 0:
            report.add_detail(f"Account '{account_address}' has no Mango Markets margin accounts.")
        else:
            for account in accounts:
                report.add_detail(f"Margin account: {account}")

        return report

    # It would be good to be able to fix an account automatically, which should
    # be possible if a Wallet is passed.
    def prepare_wallet_for_group(self, wallet: Wallet, group: Group) -> ScoutReport:
        report = ScoutReport(wallet.address)
        report.add_error("AccountScout can't yet prepare wallets.")
        return report
