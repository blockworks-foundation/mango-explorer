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
from .spotmarketinfo import SpotMarketInfo
from .token import SolToken
from .tokeninfo import TokenInfo
from .tokenlookup import TokenLookup
from .tokenvalue import TokenValue
from .version import Version


# # 🥭 Group class
#
# `Group` defines root functionality for Mango Markets.
#

class Group(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version, name: str,
                 meta_data: Metadata, tokens: typing.Sequence[typing.Optional[TokenInfo]],
                 spot_markets: typing.Sequence[typing.Optional[SpotMarketInfo]],
                 perp_markets: typing.Sequence[typing.Optional[PerpMarketInfo]],
                 oracles: typing.Sequence[PublicKey], signer_nonce: Decimal, signer_key: PublicKey,
                 admin: PublicKey, dex_program_id: PublicKey, cache: PublicKey, valid_interval: Decimal):
        super().__init__(account_info)
        self.version: Version = version
        self.name: str = name

        self.meta_data: Metadata = meta_data
        self.tokens: typing.Sequence[typing.Optional[TokenInfo]] = tokens
        self.spot_markets: typing.Sequence[typing.Optional[SpotMarketInfo]] = spot_markets
        self.perp_markets: typing.Sequence[typing.Optional[PerpMarketInfo]] = perp_markets
        self.oracles: typing.Sequence[PublicKey] = oracles
        self.signer_nonce: Decimal = signer_nonce
        self.signer_key: PublicKey = signer_key
        self.admin: PublicKey = admin
        self.dex_program_id: PublicKey = dex_program_id
        self.cache: PublicKey = cache
        self.valid_interval: Decimal = valid_interval

    @property
    def shared_quote_token(self) -> TokenInfo:
        quote = self.tokens[-1]
        if quote is None:
            raise Exception(f"Could not find shared quote token for group '{self.name}'.")
        return quote

    @property
    def base_tokens(self) -> typing.Sequence[typing.Optional[TokenInfo]]:
        return self.tokens[:-1]

    @staticmethod
    def from_layout(layout: layouts.GROUP, name: str, account_info: AccountInfo, version: Version, token_lookup: TokenLookup, market_lookup: MarketLookup) -> "Group":
        meta_data = Metadata.from_layout(layout.meta_data)
        num_oracles = layout.num_oracles
        tokens = [TokenInfo.from_layout_or_none(t, token_lookup) for t in layout.tokens]
        spot_markets = [SpotMarketInfo.from_layout_or_none(m, market_lookup) for m in layout.spot_markets]
        perp_markets = [PerpMarketInfo.from_layout_or_none(p) for p in layout.perp_markets]
        oracles = list(layout.oracles)[:int(num_oracles)]
        signer_nonce = layout.signer_nonce
        signer_key = layout.signer_key
        admin = layout.admin
        dex_program_id = layout.dex_program_id
        cache = layout.cache
        valid_interval = layout.valid_interval

        return Group(account_info, version, name, meta_data, tokens, spot_markets, perp_markets, oracles, signer_nonce, signer_key, admin, dex_program_id, cache, valid_interval)

    @staticmethod
    def parse(context: Context, account_info: AccountInfo) -> "Group":
        data = account_info.data
        if len(data) != layouts.GROUP.sizeof():
            raise Exception(
                f"Group data length ({len(data)}) does not match expected size ({layouts.GROUP.sizeof()}")

        layout = layouts.GROUP.parse(data)
        name = context.lookup_group_name(account_info.address)
        return Group.from_layout(layout, name, account_info, Version.V1, context.token_lookup, context.market_lookup)

    @staticmethod
    def load(context: Context, address: typing.Optional[PublicKey] = None) -> "Group":
        group_address: PublicKey = address or context.group_id
        account_info = AccountInfo.load(context, group_address)
        if account_info is None:
            raise Exception(f"Group account not found at address '{group_address}'")
        return Group.parse(context, account_info)

    def fetch_balances(self, context: Context, root_address: PublicKey) -> typing.Sequence[TokenValue]:
        balances: typing.List[TokenValue] = []
        sol_balance = context.fetch_sol_balance(root_address)
        balances += [TokenValue(SolToken, sol_balance)]

        for basket_token in self.tokens:
            if basket_token is not None and basket_token.token is not None:
                balance = TokenValue.fetch_total_value(context, root_address, basket_token.token)
                balances += [balance]
        return balances

    def __str__(self):
        tokens = "\n        ".join([f"{token}".replace("\n", "\n        ")
                                   for token in self.tokens if token is not None])
        spot_markets = "\n        ".join([f"{spot_market}".replace("\n", "\n        ")
                                         for spot_market in self.spot_markets if spot_market is not None])
        perp_markets = "\n        ".join([f"{perp_market}".replace("\n", "\n        ")
                                         for perp_market in self.perp_markets if perp_market is not None])
        oracles = "\n        ".join([f"{oracle}" for oracle in self.oracles])
        return f"""« 𝙶𝚛𝚘𝚞𝚙 {self.version} [{self.address}]
    {self.meta_data}
    Name: {self.name}
    Signer [Nonce: {self.signer_nonce}]: {self.signer_key}
    Admin: {self.admin}
    DEX Program ID: {self.dex_program_id}
    Merps Cache: {self.cache}
    Valid Interval: {self.valid_interval}
    Tokens:
        {tokens}
    Spot Markets:
        {spot_markets}
    Perp Markets:
        {perp_markets}
    Oracles:
        {oracles}
»"""
