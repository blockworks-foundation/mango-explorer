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

from datetime import datetime
from decimal import Decimal
from solana.publickey import PublicKey

from .accountinfo import AccountInfo
from .addressableaccount import AddressableAccount
from .context import Context
from .group import Group
from .layouts import layouts
from .metadata import Metadata
from .tokeninfo import TokenInfo
from .version import Version

# # 🥭 PerpMarket class
#
# `PerpMarket` holds details of a particular perp market.
#


class PerpMarket(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version,
                 meta_data: Metadata, group: Group, bids: PublicKey, asks: PublicKey,
                 event_queue: PublicKey, long_funding: Decimal, short_funding: Decimal,
                 open_interest: Decimal, quote_lot_size: Decimal, index_oracle: PublicKey,
                 last_updated: datetime, seq_num: Decimal, contract_size: Decimal
                 ):
        super().__init__(account_info)
        self.version: Version = version

        self.meta_data: Metadata = meta_data
        self.group: Group = group
        self.bids: PublicKey = bids
        self.asks: PublicKey = asks
        self.event_queue: PublicKey = event_queue
        self.long_funding: Decimal = long_funding
        self.short_funding: Decimal = short_funding
        self.open_interest: Decimal = open_interest
        self.quote_lot_size: Decimal = quote_lot_size
        self.index_oracle: PublicKey = index_oracle
        self.last_updated: datetime = last_updated
        self.seq_num: Decimal = seq_num
        self.contract_size: Decimal = contract_size

        market_index = -1
        for index, pm in enumerate(group.perp_markets):
            if pm is not None and pm.address == self.address:
                market_index = index
        if market_index == -1:
            raise Exception(f"Could not find perp market {self.address} in group {group.address}")

        base_token = group.tokens[market_index]
        if base_token is None:
            raise Exception(f"Could not find base token at index {market_index} for perp market {self.address}.")
        self.base_token: TokenInfo = base_token

        quote_token = group.tokens[-1]
        if quote_token is None:
            raise Exception(f"Could not find shared quote token for perp market {self.address}.")
        self.quote_token: TokenInfo = quote_token

    @staticmethod
    def from_layout(layout: layouts.PERP_MARKET, account_info: AccountInfo, version: Version, group: Group) -> "PerpMarket":
        meta_data = Metadata.from_layout(layout.meta_data)
        bids: PublicKey = layout.bids
        asks: PublicKey = layout.asks
        event_queue: PublicKey = layout.event_queue
        long_funding: Decimal = layout.long_funding
        short_funding: Decimal = layout.short_funding
        open_interest: Decimal = layout.open_interest
        quote_lot_size: Decimal = layout.quote_lot_size
        index_oracle: PublicKey = layout.index_oracle
        last_updated: datetime = layout.last_updated
        seq_num: Decimal = layout.seq_num
        contract_size: Decimal = layout.contract_size

        return PerpMarket(account_info, version, meta_data, group, bids, asks, event_queue, long_funding, short_funding, open_interest, quote_lot_size, index_oracle, last_updated, seq_num, contract_size)

    @staticmethod
    def parse(account_info: AccountInfo, group: Group) -> "PerpMarket":
        data = account_info.data
        if len(data) != layouts.PERP_MARKET.sizeof():
            raise Exception(
                f"PerpMarket data length ({len(data)}) does not match expected size ({layouts.PERP_MARKET.sizeof()}")

        layout = layouts.PERP_MARKET.parse(data)
        return PerpMarket.from_layout(layout, account_info, Version.V1, group)

    @staticmethod
    def load(context: Context, group: Group, address: PublicKey) -> "PerpMarket":
        account_info = AccountInfo.load(context, address)
        if account_info is None:
            raise Exception(f"PerpMarket account not found at address '{address}'")
        return PerpMarket.parse(account_info, group)

    def __str__(self):
        return f"""« 𝙿𝚎𝚛𝚙𝙼𝚊𝚛𝚔𝚎𝚝 {self.version} [{self.address}]
    {self.meta_data}
    Group: {self.group}
    Bids: {self.bids}
    Asks: {self.asks}
    Event Queue: {self.event_queue}
    Long Funding: {self.long_funding}
    Short Funding: {self.short_funding}
    Open Interest: {self.open_interest}
    Quote Lot Size: {self.quote_lot_size}
    Index Oracle: {self.index_oracle}
    Last Updated: {self.last_updated}
    Seq Num: {self.seq_num}
    Contract Size: {self.contract_size}
»"""
