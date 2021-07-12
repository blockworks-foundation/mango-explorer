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
                 event_queue: PublicKey, base_lot_size: Decimal, quote_lot_size: Decimal, long_funding: Decimal,
                 short_funding: Decimal, open_interest: Decimal, last_updated: datetime, seq_num: Decimal,
                 fees_accrued: Decimal, max_depth_bips: Decimal, scaler: PublicKey,
                 total_liquidity_points: Decimal):
        super().__init__(account_info)
        self.version: Version = version

        self.meta_data: Metadata = meta_data
        self.group: Group = group
        self.bids: PublicKey = bids
        self.asks: PublicKey = asks
        self.event_queue: PublicKey = event_queue
        self.base_lot_size: Decimal = base_lot_size
        self.quote_lot_size: Decimal = quote_lot_size
        self.long_funding: Decimal = long_funding
        self.short_funding: Decimal = short_funding
        self.open_interest: Decimal = open_interest
        self.last_updated: datetime = last_updated
        self.seq_num: Decimal = seq_num
        self.fees_accrued: Decimal = fees_accrued
        self.max_depth_bips: Decimal = max_depth_bips
        self.scaler: PublicKey = scaler
        self.total_liquidity_points: Decimal = total_liquidity_points

        self.market_index = group.find_perp_market_index(self.address)

        base_token = group.tokens[self.market_index]
        if base_token is None:
            raise Exception(f"Could not find base token at index {self.market_index} for perp market {self.address}.")
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
        base_lot_size: Decimal = layout.base_lot_size
        quote_lot_size: Decimal = layout.quote_lot_size

        long_funding: Decimal = layout.long_funding
        short_funding: Decimal = layout.short_funding
        open_interest: Decimal = layout.open_interest
        last_updated: datetime = layout.last_updated
        seq_num: Decimal = layout.seq_num

        fees_accrued: Decimal = layout.fees_accrued
        max_depth_bips: Decimal = layout.max_depth_bips
        scaler: PublicKey = layout.scaler
        total_liquidity_points: Decimal = layout.total_liquidity_points

        return PerpMarket(account_info, version, meta_data, group, bids, asks, event_queue,
                          base_lot_size, quote_lot_size, long_funding, short_funding, open_interest,
                          last_updated, seq_num, fees_accrued, max_depth_bips, scaler, total_liquidity_points)

    @staticmethod
    def parse(account_info: AccountInfo, group: Group) -> "PerpMarket":
        data = account_info.data
        if len(data) != layouts.PERP_MARKET.sizeof():
            raise Exception(
                f"PerpMarket data length ({len(data)}) does not match expected size ({layouts.PERP_MARKET.sizeof()})")

        layout = layouts.PERP_MARKET.parse(data)
        return PerpMarket.from_layout(layout, account_info, Version.V1, group)

    @staticmethod
    def load(context: Context, address: PublicKey, group: Group) -> "PerpMarket":
        account_info = AccountInfo.load(context, address)
        if account_info is None:
            raise Exception(f"PerpMarket account not found at address '{address}'")
        return PerpMarket.parse(account_info, group)

    def __str__(self):
        return f"""« 𝙿𝚎𝚛𝚙𝙼𝚊𝚛𝚔𝚎𝚝 {self.version} [{self.address}]
    {self.meta_data}
    Group: {self.group.address}
    Bids: {self.bids}
    Asks: {self.asks}
    Event Queue: {self.event_queue}
    Long Funding: {self.long_funding}
    Short Funding: {self.short_funding}
    Open Interest: {self.open_interest}
    Base Lot Size: {self.base_lot_size}
    Quote Lot Size: {self.quote_lot_size}
    Last Updated: {self.last_updated}
    Seq Num: {self.seq_num}
    Fees Accrued: {self.fees_accrued}
    Max Depth Bips: {self.max_depth_bips}
    Scaler: {self.scaler}
    Total Liquidity Points: {self.total_liquidity_points}
»"""
