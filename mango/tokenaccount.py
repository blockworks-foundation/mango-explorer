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

from solana.account import Account
from solana.publickey import PublicKey
from solana.rpc.types import TokenAccountOpts
from spl.token.client import Token as SplToken
from spl.token.constants import TOKEN_PROGRAM_ID

from .accountinfo import AccountInfo
from .addressableaccount import AddressableAccount
from .context import Context
from .layouts import layouts
from .token import Token
from .tokenlookup import TokenLookup
from .tokenvalue import TokenValue
from .version import Version

# # 🥭 TokenAccount class
#


class TokenAccount(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version, owner: PublicKey, value: TokenValue):
        super().__init__(account_info)
        self.version: Version = version
        self.owner: PublicKey = owner
        self.value: TokenValue = value

    @staticmethod
    def create(context: Context, account: Account, token: Token):
        spl_token = SplToken(context.client.compatible_client, token.mint, TOKEN_PROGRAM_ID, account)
        owner = account.public_key()
        new_account_address = spl_token.create_account(owner)
        return TokenAccount.load(context, new_account_address)

    @staticmethod
    def fetch_all_for_owner_and_token(context: Context, owner_public_key: PublicKey, token: Token) -> typing.List["TokenAccount"]:
        opts = TokenAccountOpts(mint=token.mint)

        token_accounts = context.client.get_token_accounts_by_owner(owner_public_key, opts)

        all_accounts: typing.List[TokenAccount] = []
        for token_account_response in token_accounts:
            account_info = AccountInfo._from_response_values(
                token_account_response["account"], PublicKey(token_account_response["pubkey"]))
            token_account = TokenAccount.parse(account_info, token)
            all_accounts += [token_account]

        return all_accounts

    @staticmethod
    def fetch_largest_for_owner_and_token(context: Context, owner_public_key: PublicKey, token: Token) -> typing.Optional["TokenAccount"]:
        all_accounts = TokenAccount.fetch_all_for_owner_and_token(context, owner_public_key, token)

        largest_account: typing.Optional[TokenAccount] = None
        for token_account in all_accounts:
            if largest_account is None or token_account.value.value > largest_account.value.value:
                largest_account = token_account

        return largest_account

    @staticmethod
    def fetch_or_create_largest_for_owner_and_token(context: Context, account: Account, token: Token) -> "TokenAccount":
        all_accounts = TokenAccount.fetch_all_for_owner_and_token(context, account.public_key(), token)

        largest_account: typing.Optional[TokenAccount] = None
        for token_account in all_accounts:
            if largest_account is None or token_account.value.value > largest_account.value.value:
                largest_account = token_account

        if largest_account is None:
            return TokenAccount.create(context, account, token)

        return largest_account

    @staticmethod
    def from_layout(layout: layouts.TOKEN_ACCOUNT, account_info: AccountInfo, token: Token) -> "TokenAccount":
        token_value = TokenValue(token, token.shift_to_decimals(layout.amount))
        return TokenAccount(account_info, Version.UNSPECIFIED, layout.owner, token_value)

    @staticmethod
    def parse(account_info: AccountInfo, token: typing.Optional[Token] = None, token_lookup: typing.Optional[TokenLookup] = None) -> "TokenAccount":
        data = account_info.data
        if len(data) != layouts.TOKEN_ACCOUNT.sizeof():
            raise Exception(
                f"Data length ({len(data)}) does not match expected size ({layouts.TOKEN_ACCOUNT.sizeof()})")

        layout = layouts.TOKEN_ACCOUNT.parse(data)
        if token is None:
            if token_lookup is None:
                raise Exception("Neither 'Token' or 'TokenLookup' specified for parsing token data.")
            token = token_lookup.find_by_mint(layout.mint)
            if token is None:
                raise Exception(f"Could not find token data for token with mint '{layout.mint}'")

        return TokenAccount.from_layout(layout, account_info, token)

    @staticmethod
    def load(context: Context, address: PublicKey) -> typing.Optional["TokenAccount"]:
        account_info = AccountInfo.load(context, address)
        if account_info is None or (len(account_info.data) != layouts.TOKEN_ACCOUNT.sizeof()):
            return None
        return TokenAccount.parse(account_info, token_lookup=context.token_lookup)

    def __str__(self) -> str:
        return f"« Token: Address: {self.address}, Owner: {self.owner}, Value: {self.value} »"
