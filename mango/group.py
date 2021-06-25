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

import construct
import time
import typing

from decimal import Decimal
from solana.publickey import PublicKey

from .accountinfo import AccountInfo
from .addressableaccount import AddressableAccount
from .aggregator import Aggregator
from .baskettoken import BasketToken
from .context import Context
from .index import Index
from .layouts import layouts
from .mangoaccountflags import MangoAccountFlags
from .marketmetadata import MarketMetadata
from .marketlookup import MarketLookup
from .token import SolToken, Token
from .tokenlookup import TokenLookup
from .tokenvalue import TokenValue
from .version import Version

# # 🥭 Group class
#
# The `Group` class encapsulates the data for the Mango Group - the cross-margined basket
# of tokens with lending.


class Group(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version, name: str,
                 account_flags: MangoAccountFlags, basket_tokens: typing.List[BasketToken],
                 markets: typing.List[MarketMetadata],
                 signer_nonce: Decimal, signer_key: PublicKey, dex_program_id: PublicKey,
                 total_deposits: typing.List[TokenValue], total_borrows: typing.List[TokenValue],
                 maint_coll_ratio: Decimal, init_coll_ratio: Decimal, srm_vault: PublicKey,
                 admin: PublicKey, borrow_limits: typing.List[TokenValue]):
        super().__init__(account_info)
        self.version: Version = version
        self.name: str = name
        self.account_flags: MangoAccountFlags = account_flags
        self.basket_tokens: typing.List[BasketToken] = basket_tokens
        self.markets: typing.List[MarketMetadata] = markets
        self.signer_nonce: Decimal = signer_nonce
        self.signer_key: PublicKey = signer_key
        self.dex_program_id: PublicKey = dex_program_id
        self.total_deposits: typing.List[TokenValue] = total_deposits
        self.total_borrows: typing.List[TokenValue] = total_borrows
        self.maint_coll_ratio: Decimal = maint_coll_ratio
        self.init_coll_ratio: Decimal = init_coll_ratio
        self.srm_vault: PublicKey = srm_vault
        self.admin: PublicKey = admin
        self.borrow_limits: typing.List[TokenValue] = borrow_limits

    @property
    def shared_quote_token(self) -> BasketToken:
        return self.basket_tokens[-1]

    @property
    def base_tokens(self) -> typing.List[BasketToken]:
        return self.basket_tokens[:-1]

    # When loading from a layout, we ignore mint_decimals. In this Discord from Daffy:
    #   https://discord.com/channels/791995070613159966/818978757648842782/851481660049850388
    # he says it's:
    # > same as what is stored on on chain Mint
    # > Cached on the group so we don't have to pass in the mint every time
    #
    # Since we already have that value from our `Token` we don't need to use it and we can
    # stick with passing around `Token` objects.
    #
    @staticmethod
    def from_layout(layout: construct.Struct, name: str, account_info: AccountInfo, version: Version, token_lookup: TokenLookup, market_lookup: MarketLookup) -> "Group":
        account_flags: MangoAccountFlags = MangoAccountFlags.from_layout(layout.account_flags)

        basket_tokens: typing.List[BasketToken] = []
        total_deposits: typing.List[TokenValue] = []
        total_borrows: typing.List[TokenValue] = []
        borrow_limits: typing.List[TokenValue] = []
        for index, token_address in enumerate(layout.tokens):
            static_token_data = token_lookup.find_by_mint(token_address)
            if static_token_data is None:
                raise Exception(f"Could not find token with mint '{token_address}'.")

            # We create a new Token object here specifically to force the use of our own decimals
            token = Token(static_token_data.symbol, static_token_data.name, token_address, layout.mint_decimals[index])
            token_index = Index.from_layout(layout.indexes[index], token)
            basket_token = BasketToken(token, layout.vaults[index], token_index)
            basket_tokens += [basket_token]
            total_deposits += [TokenValue(token, token.shift_to_decimals(layout.total_deposits[index]))]
            total_borrows += [TokenValue(token, token.shift_to_decimals(layout.total_borrows[index]))]
            borrow_limits += [TokenValue(token, token.shift_to_decimals(layout.borrow_limits[index]))]

        markets: typing.List[MarketMetadata] = []
        for index, market_address in enumerate(layout.spot_markets):
            spot_market = market_lookup.find_by_address(market_address)
            if spot_market is None:
                raise Exception(f"Could not find spot market with address '{market_address}'.")

            base_token = BasketToken.find_by_mint(basket_tokens, spot_market.base.mint)
            quote_token = BasketToken.find_by_mint(basket_tokens, spot_market.quote.mint)

            market = MarketMetadata(spot_market.symbol, market_address, base_token, quote_token,
                                    spot_market, layout.oracles[index], layout.oracle_decimals[index])
            markets += [market]

        maint_coll_ratio = layout.maint_coll_ratio.quantize(Decimal('.01'))
        init_coll_ratio = layout.init_coll_ratio.quantize(Decimal('.01'))

        return Group(account_info, version, name, account_flags, basket_tokens, markets,
                     layout.signer_nonce, layout.signer_key, layout.dex_program_id, total_deposits,
                     total_borrows, maint_coll_ratio, init_coll_ratio, layout.srm_vault,
                     layout.admin, borrow_limits)

    @staticmethod
    def parse(context: Context, account_info: AccountInfo) -> "Group":
        data = account_info.data
        if len(data) == layouts.GROUP_V1.sizeof():
            layout = layouts.GROUP_V1.parse(data)
            version: Version = Version.V1
        elif len(data) == layouts.GROUP_V2.sizeof():
            version = Version.V2
            layout = layouts.GROUP_V2.parse(data)
        else:
            raise Exception(
                f"Group data length ({len(data)}) does not match expected size ({layouts.GROUP_V1.sizeof()} or {layouts.GROUP_V2.sizeof()})")

        return Group.from_layout(layout, context.group_name, account_info, version, context.token_lookup, context.market_lookup)

    @staticmethod
    def load(context: Context):
        account_info = AccountInfo.load(context, context.group_id)
        if account_info is None:
            raise Exception(f"Group account not found at address '{context.group_id}'")
        return Group.parse(context, account_info)

    def price_index_of_token(self, token: Token) -> int:
        for index, existing in enumerate(self.basket_tokens):
            if existing.token == token:
                return index
        return -1

    def fetch_token_prices(self, context: Context) -> typing.List[TokenValue]:
        started_at = time.time()

        # Note: we can just load the oracle data in a simpler way, with:
        #   oracles = map(lambda market: Aggregator.load(context, market.oracle), self.markets)
        # but that makes a network request for every oracle. We can reduce that to just one request
        # if we use AccountInfo.load_multiple() and parse the data ourselves.
        #
        # This seems to halve the time this function takes.
        oracle_addresses = list([market.oracle for market in self.markets])
        oracle_account_infos = AccountInfo.load_multiple(context, oracle_addresses)
        oracles = map(lambda oracle_account_info: Aggregator.parse(context, oracle_account_info), oracle_account_infos)
        prices = list(map(lambda oracle: oracle.price, oracles)) + [Decimal(1)]
        token_prices = []
        for index, price in enumerate(prices):
            token_prices += [TokenValue(self.basket_tokens[index].token, price)]

        time_taken = time.time() - started_at
        self.logger.info(f"Fetching prices complete. Time taken: {time_taken:.2f} seconds.")
        return token_prices

    @staticmethod
    def load_with_prices(context: Context) -> typing.Tuple["Group", typing.List[TokenValue]]:
        group = Group.load(context)
        prices = group.fetch_token_prices(context)
        return group, prices

    def fetch_balances(self, context: Context, root_address: PublicKey) -> typing.List[TokenValue]:
        balances: typing.List[TokenValue] = []
        sol_balance = context.fetch_sol_balance(root_address)
        balances += [TokenValue(SolToken, sol_balance)]

        for basket_token in self.basket_tokens:
            balance = TokenValue.fetch_total_value(context, root_address, basket_token.token)
            balances += [balance]
        return balances

    def __str__(self) -> str:
        total_deposits = "\n        ".join(map(str, self.total_deposits))
        total_borrows = "\n        ".join(map(str, self.total_borrows))
        borrow_limits = "\n        ".join(map(str, self.borrow_limits))
        shared_quote_token = str(self.shared_quote_token).replace("\n", "\n        ")
        base_tokens = "\n        ".join([f"{tok}".replace("\n", "\n        ") for tok in self.base_tokens])
        markets = "\n        ".join([f"{mkt}".replace("\n", "\n        ") for mkt in self.markets])
        return f"""
« Group [{self.version} - {self.name}] {self.address}:
    Flags: {self.account_flags}
    Base Tokens:
        {base_tokens}
    Quote Token:
        {shared_quote_token}
    Markets:
        {markets}
    DEX Program ID: « {self.dex_program_id} »
    SRM Vault: « {self.srm_vault} »
    Admin: « {self.admin} »
    Signer Nonce: {self.signer_nonce}
    Signer Key: « {self.signer_key} »
    Initial Collateral Ratio: {self.init_coll_ratio}
    Maintenance Collateral Ratio: {self.maint_coll_ratio}
    Total Deposits:
        {total_deposits}
    Total Borrows:
        {total_borrows}
    Borrow Limits:
        {borrow_limits}
»
"""
