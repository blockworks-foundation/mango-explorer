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
from .addressableaccount import AddressableAccount
from .context import Context
from .layouts import layouts
from .marketlookup import MarketLookup
from .metadata import Metadata
from .perpmarketinfo import PerpMarketInfo
from .rootbank import RootBank
from .spotmarketinfo import SpotMarketInfo
from .token import SolToken, Token
from .tokeninfo import TokenInfo
from .tokenlookup import TokenLookup
from .tokenvalue import TokenValue
from .version import Version


# # 🥭 GroupBasketMarket class
#
# `GroupBasketMarket` gathers basket items together instead of separate arrays.
#
class GroupBasketMarket:
    def __init__(self, base_token_info: TokenInfo, quote_token_info: TokenInfo, spot_market_info: SpotMarketInfo, perp_market_info: PerpMarketInfo, oracle: PublicKey):
        self.base_token_info: TokenInfo = base_token_info
        self.quote_token_info: TokenInfo = quote_token_info
        self.spot_market_info: SpotMarketInfo = spot_market_info
        self.perp_market_info: PerpMarketInfo = perp_market_info
        self.oracle: PublicKey = oracle

    def __str__(self) -> str:
        base_token_info = f"{self.base_token_info}".replace("\n", "\n        ")
        quote_token_info = f"{self.quote_token_info}".replace("\n", "\n        ")
        spot_market_info = f"{self.spot_market_info}".replace("\n", "\n        ")
        perp_market_info = f"{self.perp_market_info}".replace("\n", "\n        ")
        return f"""« 𝙶𝚛𝚘𝚞𝚙𝙱𝚊𝚜𝚔𝚎𝚝𝙼𝚊𝚛𝚔𝚎𝚝 {self.base_token_info.token.symbol}
    Base Token:
        {base_token_info}
    Quote Token:
        {quote_token_info}
    Oracle: {self.oracle}
    Spot Market:
        {spot_market_info}
    Perp Market:
        {perp_market_info}
»"""

    def __repr__(self) -> str:
        return f"{self}"


TMappedGroupBasketValue = typing.TypeVar("TMappedGroupBasketValue")


# # 🥭 Group class
#
# `Group` defines root functionality for Mango Markets.
#

class Group(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version, name: str,
                 meta_data: Metadata,
                 shared_quote_token: TokenInfo,
                 basket_indices: typing.Sequence[bool],
                 basket: typing.Sequence[GroupBasketMarket],
                 signer_nonce: Decimal, signer_key: PublicKey,
                 admin: PublicKey, dex_program_id: PublicKey, cache: PublicKey, valid_interval: Decimal,
                 dao_vault: PublicKey, srm_vault: PublicKey, msrm_vault: PublicKey):
        super().__init__(account_info)
        self.version: Version = version
        self.name: str = name

        self.meta_data: Metadata = meta_data
        self.shared_quote_token: TokenInfo = shared_quote_token
        self.basket_indices: typing.Sequence[bool] = basket_indices
        self.basket: typing.Sequence[GroupBasketMarket] = basket
        self.signer_nonce: Decimal = signer_nonce
        self.signer_key: PublicKey = signer_key
        self.admin: PublicKey = admin
        self.dex_program_id: PublicKey = dex_program_id
        self.cache: PublicKey = cache
        self.valid_interval: Decimal = valid_interval
        self.dao_vault: PublicKey = dao_vault
        self.srm_vault: PublicKey = srm_vault
        self.msrm_vault: PublicKey = msrm_vault

    @property
    def base_tokens(self) -> typing.Sequence[typing.Optional[TokenInfo]]:
        return Group._map_sequence_to_basket_indices(self.basket, self.basket_indices, lambda item: item.base_token_info)

    @property
    def tokens(self) -> typing.Sequence[typing.Optional[TokenInfo]]:
        return [*self.base_tokens, self.shared_quote_token]

    @property
    def oracles(self) -> typing.Sequence[typing.Optional[PublicKey]]:
        return Group._map_sequence_to_basket_indices(self.basket, self.basket_indices, lambda item: item.oracle)

    @property
    def spot_markets(self) -> typing.Sequence[typing.Optional[SpotMarketInfo]]:
        return Group._map_sequence_to_basket_indices(self.basket, self.basket_indices, lambda item: item.spot_market_info)

    @property
    def perp_markets(self) -> typing.Sequence[typing.Optional[PerpMarketInfo]]:
        return Group._map_sequence_to_basket_indices(self.basket, self.basket_indices, lambda item: item.perp_market_info)

    @staticmethod
    def from_layout(context: Context, layout: layouts.GROUP, name: str, account_info: AccountInfo, version: Version, token_lookup: TokenLookup, market_lookup: MarketLookup) -> "Group":
        meta_data: Metadata = Metadata.from_layout(layout.meta_data)

        root_bank_addresses = [ti.root_bank for ti in layout.tokens if ti is not None and ti.root_bank is not None]
        root_banks = RootBank.load_multiple(context, root_bank_addresses)
        tokens: typing.List[typing.Optional[TokenInfo]] = [
            TokenInfo.from_layout_or_none(t, token_lookup, root_banks) for t in layout.tokens]

        quote_token_info: typing.Optional[TokenInfo] = tokens[-1]
        if quote_token_info is None:
            raise Exception("Could not find quote token info at end of group tokens.")
        basket: typing.List[GroupBasketMarket] = []
        in_basket: typing.List[bool] = []
        for index, base_token_info in enumerate(tokens[:-1]):
            if base_token_info is not None:
                spot_market_info: SpotMarketInfo = SpotMarketInfo.from_layout(layout.spot_markets[index])
                perp_market_info: PerpMarketInfo = PerpMarketInfo.from_layout(layout.perp_markets[index])
                oracle: PublicKey = layout.oracles[index]
                item: GroupBasketMarket = GroupBasketMarket(
                    base_token_info, quote_token_info, spot_market_info, perp_market_info, oracle)
                basket += [item]
                in_basket += [True]
            else:
                in_basket += [False]

        signer_nonce: Decimal = layout.signer_nonce
        signer_key: PublicKey = layout.signer_key
        admin: PublicKey = layout.admin
        dex_program_id: PublicKey = layout.dex_program_id
        cache: PublicKey = layout.cache
        valid_interval: Decimal = layout.valid_interval
        dao_vault: PublicKey = layout.dao_vault
        srm_vault: PublicKey = layout.srm_vault
        msrm_vault: PublicKey = layout.msrm_vault

        return Group(account_info, version, name, meta_data, quote_token_info, in_basket, basket, signer_nonce, signer_key, admin, dex_program_id, cache, valid_interval, dao_vault, srm_vault, msrm_vault)

    @staticmethod
    def parse(context: Context, account_info: AccountInfo) -> "Group":
        data = account_info.data
        if len(data) != layouts.GROUP.sizeof():
            raise Exception(
                f"Group data length ({len(data)}) does not match expected size ({layouts.GROUP.sizeof()})")

        layout = layouts.GROUP.parse(data)
        name = context.lookup_group_name(account_info.address)
        return Group.from_layout(context, layout, name, account_info, Version.V3, context.token_lookup, context.market_lookup)

    @staticmethod
    def _map_sequence_to_basket_indices(items: typing.Sequence[GroupBasketMarket], in_basket: typing.Sequence[bool], selector: typing.Callable[[typing.Any], TMappedGroupBasketValue]) -> typing.Sequence[typing.Optional[TMappedGroupBasketValue]]:
        mapped_items: typing.List[typing.Optional[TMappedGroupBasketValue]] = []
        basket_counter = 0
        for available in in_basket:
            if available:
                mapped_items += [selector(items[basket_counter])]
                basket_counter += 1
            else:
                mapped_items += [None]

        return mapped_items

    @staticmethod
    def load(context: Context, address: typing.Optional[PublicKey] = None) -> "Group":
        group_address: PublicKey = address or context.group_id
        account_info = AccountInfo.load(context, group_address)
        if account_info is None:
            raise Exception(f"Group account not found at address '{group_address}'")
        return Group.parse(context, account_info)

    def find_spot_market_index(self, spot_market_address: PublicKey) -> int:
        for index, spot in enumerate(self.spot_markets):
            if spot is not None and spot.address == spot_market_address:
                return index

        raise Exception(f"Could not find spot market {spot_market_address} in group {self.address}")

    def find_perp_market_index(self, perp_market_address: PublicKey) -> int:
        for index, pm in enumerate(self.perp_markets):
            if pm is not None and pm.address == perp_market_address:
                return index

        raise Exception(f"Could not find perp market {perp_market_address} in group {self.address}")

    def find_token_info_by_token(self, token: Token) -> TokenInfo:
        for token_info in self.tokens:
            if token_info is not None and token_info.token == token:
                return token_info

        raise Exception(f"Could not find token info for mint {token.mint} in group {self.address}")

    def fetch_balances(self, context: Context, root_address: PublicKey) -> typing.Sequence[TokenValue]:
        balances: typing.List[TokenValue] = []
        sol_balance = context.fetch_sol_balance(root_address)
        balances += [TokenValue(SolToken, sol_balance)]

        for basket_token in self.tokens:
            if basket_token is not None and basket_token.token is not None:
                balance = TokenValue.fetch_total_value(context, root_address, basket_token.token)
                balances += [balance]
        return balances

    def __str__(self) -> str:
        basket_count = len(self.basket)
        basket = "\n        ".join([f"{item}".replace("\n", "\n        ") for item in self.basket])
        return f"""« 𝙶𝚛𝚘𝚞𝚙 {self.version} [{self.address}]
    {self.meta_data}
    Name: {self.name}
    Signer [Nonce: {self.signer_nonce}]: {self.signer_key}
    Admin: {self.admin}
    DEX Program ID: {self.dex_program_id}
    Cache: {self.cache}
    DAO Vault: {self.dao_vault}
    SRM Vault: {self.srm_vault}
    MSRM Vault: {self.msrm_vault}
    Valid Interval: {self.valid_interval}
    Basket [{basket_count} markets]:
        {basket}
»"""
