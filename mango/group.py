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
from .cache import Cache, PriceCache, PerpMarketCache
from .context import Context
from .layouts import layouts
from .lotsizeconverter import LotSizeConverter, RaisingLotSizeConverter

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
    def __init__(self, base_token_info: TokenInfo, quote_token_info: TokenInfo, spot_market_info: SpotMarketInfo, perp_market_info: typing.Optional[PerpMarketInfo], perp_lot_size_converter: LotSizeConverter, oracle: PublicKey):
        self.base_token_info: TokenInfo = base_token_info
        self.quote_token_info: TokenInfo = quote_token_info
        self.spot_market_info: SpotMarketInfo = spot_market_info
        self.perp_market_info: typing.Optional[PerpMarketInfo] = perp_market_info
        self.perp_lot_size_converter: LotSizeConverter = perp_lot_size_converter
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
                 admin: PublicKey, serum_program_address: PublicKey, cache: PublicKey, valid_interval: Decimal,
                 insurance_vault: PublicKey, srm_vault: PublicKey, msrm_vault: PublicKey, fees_vault: PublicKey):
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
        self.serum_program_address: PublicKey = serum_program_address
        self.cache: PublicKey = cache
        self.valid_interval: Decimal = valid_interval
        self.insurance_vault: PublicKey = insurance_vault
        self.srm_vault: PublicKey = srm_vault
        self.msrm_vault: PublicKey = msrm_vault
        self.fees_vault: PublicKey = fees_vault

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

    @property
    def markets(self) -> typing.Sequence[typing.Optional[GroupBasketMarket]]:
        return Group._map_sequence_to_basket_indices(self.basket, self.basket_indices, lambda item: item)

    @staticmethod
    def from_layout(layout: typing.Any, name: str, account_info: AccountInfo, version: Version, root_banks: typing.Sequence[RootBank], token_lookup: TokenLookup) -> "Group":
        meta_data: Metadata = Metadata.from_layout(layout.meta_data)
        tokens: typing.List[typing.Optional[TokenInfo]] = [
            TokenInfo.from_layout_or_none(t, token_lookup, root_banks) for t in layout.tokens]

        quote_token_info: typing.Optional[TokenInfo] = tokens[-1]
        if quote_token_info is None:
            raise Exception("Could not find quote token info at end of group tokens.")
        basket: typing.List[GroupBasketMarket] = []
        in_basket: typing.List[bool] = []
        for index, base_token_info in enumerate(tokens[:-1]):
            if base_token_info is not None:
                spot_market_info: typing.Optional[SpotMarketInfo] = SpotMarketInfo.from_layout_or_none(
                    layout.spot_markets[index])
                if spot_market_info is None:
                    raise Exception(f"Could not find spot market at index {index} of group layout.")
                perp_market_info: typing.Optional[PerpMarketInfo] = PerpMarketInfo.from_layout_or_none(
                    layout.perp_markets[index])
                perp_lot_size_converter: LotSizeConverter = RaisingLotSizeConverter()
                if perp_market_info is not None:
                    perp_lot_size_converter = LotSizeConverter(
                        base_token_info.token, perp_market_info.base_lot_size, quote_token_info.token, perp_market_info.quote_lot_size)

                oracle: PublicKey = layout.oracles[index]
                item: GroupBasketMarket = GroupBasketMarket(
                    base_token_info, quote_token_info, spot_market_info, perp_market_info, perp_lot_size_converter, oracle)
                basket += [item]
                in_basket += [True]
            else:
                in_basket += [False]

        signer_nonce: Decimal = layout.signer_nonce
        signer_key: PublicKey = layout.signer_key
        admin: PublicKey = layout.admin
        serum_program_address: PublicKey = layout.serum_program_address
        cache: PublicKey = layout.cache
        valid_interval: Decimal = layout.valid_interval
        insurance_vault: PublicKey = layout.insurance_vault
        srm_vault: PublicKey = layout.srm_vault
        msrm_vault: PublicKey = layout.msrm_vault
        fees_vault: PublicKey = layout.fees_vault

        return Group(account_info, version, name, meta_data, quote_token_info, in_basket, basket, signer_nonce, signer_key, admin, serum_program_address, cache, valid_interval, insurance_vault, srm_vault, msrm_vault, fees_vault)

    @staticmethod
    def parse(context: Context, account_info: AccountInfo) -> "Group":
        data = account_info.data
        if len(data) != layouts.GROUP.sizeof():
            raise Exception(
                f"Group data length ({len(data)}) does not match expected size ({layouts.GROUP.sizeof()})")

        name = context.lookup_group_name(account_info.address)
        layout = layouts.GROUP.parse(data)
        root_bank_addresses = [ti.root_bank for ti in layout.tokens if ti is not None and ti.root_bank is not None]
        root_banks = RootBank.load_multiple(context, root_bank_addresses)
        return Group.parse_locally(account_info, name, root_banks, context.token_lookup)

    @staticmethod
    def parse_locally(account_info: AccountInfo, name: str, root_banks: typing.Sequence[RootBank], token_lookup: TokenLookup) -> "Group":
        data = account_info.data
        if len(data) != layouts.GROUP.sizeof():
            raise Exception(
                f"Group data length ({len(data)}) does not match expected size ({layouts.GROUP.sizeof()})")

        layout = layouts.GROUP.parse(data)
        return Group.from_layout(layout, name, account_info, Version.V3, root_banks, token_lookup)

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
        group_address: PublicKey = address or context.group_address
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

    def find_base_token_market_index(self, base_token: TokenInfo) -> int:
        for index, bt in enumerate(self.base_tokens):
            if bt is not None and bt.token == base_token.token:
                return index

        raise Exception(f"Could not find base token {base_token} in group {self.address}")

    def find_token_market_index_or_none(self, token: Token) -> typing.Optional[int]:
        for index, bt in enumerate(self.base_tokens):
            if bt is not None and bt.token == token:
                return index

        return None

    def find_token_market_index(self, token: Token) -> int:
        index = self.find_token_market_index_or_none(token)
        if index is not None:
            return index

        raise Exception(f"Could not find token {token} in group {self.address}")

    def find_token_info_by_token(self, token: Token) -> TokenInfo:
        for token_info in self.tokens:
            if token_info is not None and token_info.token == token:
                return token_info

        raise Exception(f"Could not find token info for mint {token.mint} in group {self.address}")

    def find_token_info_by_symbol(self, symbol: str) -> TokenInfo:
        for token_info in self.tokens:
            if token_info is not None and token_info.token.symbol_matches(symbol):
                return token_info

        raise Exception(f"Could not find token info for symbol '{symbol}' in group {self.address}")

    def token_price_from_cache(self, cache: Cache, token: Token) -> TokenValue:
        if token == self.shared_quote_token.token:
            # The price of 1 unit of the shared quote token is always 1.
            return TokenValue(token, Decimal(1))

        token_index: int = self.find_token_market_index(token)
        cached_price: typing.Optional[PriceCache] = cache.price_cache[token_index]
        if cached_price is None:
            raise Exception(f"Could not find price index of basket token {token.symbol}.")

        price: Decimal = cached_price.price
        decimals_difference = token.decimals - self.shared_quote_token.decimals
        if decimals_difference != 0:
            adjustment = 10 ** decimals_difference
            price = price * adjustment

        return TokenValue(self.shared_quote_token.token, price)

    def perp_market_cache_from_cache(self, cache: Cache, token: Token) -> typing.Optional[PerpMarketCache]:
        token_index: int = self.find_token_market_index(token)
        return cache.perp_market_cache[token_index]

    def fetch_balances(self, context: Context, root_address: PublicKey) -> typing.Sequence[TokenValue]:
        balances: typing.List[TokenValue] = []
        sol_balance = context.client.get_balance(root_address)
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
    DEX Program ID: {self.serum_program_address}
    Cache: {self.cache}
    Insurance Vault: {self.insurance_vault}
    SRM Vault: {self.srm_vault}
    MSRM Vault: {self.msrm_vault}
    Fees Vault: {self.fees_vault}
    Valid Interval: {self.valid_interval}
    Basket [{basket_count} markets]:
        {basket}
»"""
