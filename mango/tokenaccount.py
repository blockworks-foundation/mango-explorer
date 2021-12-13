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


import spl.token.instructions as spl_token
import typing

from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.types import TokenAccountOpts
from spl.token.client import Token as SplToken
from spl.token.constants import TOKEN_PROGRAM_ID

from .accountinfo import AccountInfo
from .addressableaccount import AddressableAccount
from .combinableinstructions import CombinableInstructions
from .context import Context
from .instrumentlookup import InstrumentLookup
from .instrumentvalue import InstrumentValue
from .layouts import layouts
from .token import Instrument, Token
from .version import Version
from .wallet import Wallet


# # 🥭 TokenAccount class
#
class TokenAccount(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version, owner: PublicKey, value: InstrumentValue) -> None:
        super().__init__(account_info)
        self.version: Version = version
        self.owner: PublicKey = owner
        self.value: InstrumentValue = value

    @staticmethod
    def create(context: Context, account: Keypair, token: Token) -> "TokenAccount":
        spl_token = SplToken(context.client.compatible_client, token.mint, TOKEN_PROGRAM_ID, account)
        owner = account.public_key
        new_account_address = spl_token.create_account(owner)
        created: typing.Optional[TokenAccount] = TokenAccount.load(context, new_account_address)
        if created is None:
            raise Exception(f"Newly-created SPL token account could not be found at address {new_account_address}")
        return created

    @staticmethod
    def fetch_all_for_owner_and_token(context: Context, owner_public_key: PublicKey, token: Token) -> typing.Sequence["TokenAccount"]:
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
    def fetch_or_create_largest_for_owner_and_token(context: Context, account: Keypair, token: Token) -> "TokenAccount":
        all_accounts = TokenAccount.fetch_all_for_owner_and_token(context, account.public_key, token)

        largest_account: typing.Optional[TokenAccount] = None
        for token_account in all_accounts:
            if largest_account is None or token_account.value.value > largest_account.value.value:
                largest_account = token_account

        if largest_account is None:
            return TokenAccount.create(context, account, token)

        return largest_account

    @staticmethod
    def find_or_create_token_address_to_use(context: Context, wallet: Wallet, owner: PublicKey, token: Token) -> PublicKey:
        # This is a root wallet account - get the token account to use.
        associated_token_address = spl_token.get_associated_token_address(owner, token.mint)
        token_account: typing.Optional[TokenAccount] = TokenAccount.load(context, associated_token_address)
        if token_account is not None:
            # The associated token account exists so use it
            return associated_token_address

        # There is no associated token account. See if they have an old-style non-associated token account.
        largest = TokenAccount.fetch_largest_for_owner_and_token(context, owner, token)
        if largest is not None:
            # There is an old-style account so use that.
            return largest.address

        # There is no old-style token account either, so create the proper associated token account.
        signer = CombinableInstructions.from_wallet(wallet)
        create_instruction = spl_token.create_associated_token_account(wallet.address, owner, token.mint)
        create = CombinableInstructions.from_instruction(create_instruction)

        transaction_ids = (signer + create).execute(context)
        context.client.wait_for_confirmation(transaction_ids)

        return associated_token_address

    @staticmethod
    def from_layout(layout: typing.Any, account_info: AccountInfo, token: Token) -> "TokenAccount":
        token_value = InstrumentValue(token, token.shift_to_decimals(layout.amount))
        return TokenAccount(account_info, Version.UNSPECIFIED, layout.owner, token_value)

    @staticmethod
    def parse(account_info: AccountInfo, token: typing.Optional[Token] = None, instrument_lookup: typing.Optional[InstrumentLookup] = None) -> "TokenAccount":
        data = account_info.data
        if len(data) != layouts.TOKEN_ACCOUNT.sizeof():
            raise Exception(
                f"Data length ({len(data)}) does not match expected size ({layouts.TOKEN_ACCOUNT.sizeof()})")

        layout = layouts.TOKEN_ACCOUNT.parse(data)
        if token is None:
            if instrument_lookup is None:
                raise Exception("Neither 'Token' or 'InstrumentLookup' specified for parsing token data.")
            instrument: typing.Optional[Instrument] = instrument_lookup.find_by_mint(layout.mint)
            if instrument is None:
                raise Exception(f"Could not find token data for token with mint '{layout.mint}'")
            token = Token.ensure(instrument)

        return TokenAccount.from_layout(layout, account_info, token)

    @staticmethod
    def load(context: Context, address: PublicKey) -> typing.Optional["TokenAccount"]:
        account_info = AccountInfo.load(context, address)
        if account_info is None or (len(account_info.data) != layouts.TOKEN_ACCOUNT.sizeof()):
            return None
        return TokenAccount.parse(account_info, instrument_lookup=context.instrument_lookup)

    def __str__(self) -> str:
        return f"« TokenAccount {self.address}, Owner: {self.owner}, Value: {self.value} »"
