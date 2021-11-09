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
from .cache import Cache, PerpMarketCache, MarketCache
from .constants import SYSTEM_PROGRAM_ADDRESS
from .context import Context
from .instrumentlookup import InstrumentLookup
from .instrumentvalue import InstrumentValue
from .layouts import layouts
from .lotsizeconverter import LotSizeConverter, RaisingLotSizeConverter
from .marketlookup import MarketLookup
from .metadata import Metadata
from .rootbank import RootBank
from .token import Instrument, Token
from .tokeninfo import TokenInfo
from .version import Version


# # 🥭 GroupSlotSpotMarket class
#
class GroupSlotSpotMarket:
    def __init__(self, address: PublicKey, maint_asset_weight: Decimal, init_asset_weight: Decimal, maint_liab_weight: Decimal, init_liab_weight: Decimal) -> None:
        self.address: PublicKey = address
        self.maint_asset_weight: Decimal = maint_asset_weight
        self.init_asset_weight: Decimal = init_asset_weight
        self.maint_liab_weight: Decimal = maint_liab_weight
        self.init_liab_weight: Decimal = init_liab_weight

    @staticmethod
    def from_layout(layout: typing.Any) -> "GroupSlotSpotMarket":
        spot_market: PublicKey = layout.spot_market
        maint_asset_weight: Decimal = round(layout.maint_asset_weight, 8)
        init_asset_weight: Decimal = round(layout.init_asset_weight, 8)
        maint_liab_weight: Decimal = round(layout.maint_liab_weight, 8)
        init_liab_weight: Decimal = round(layout.init_liab_weight, 8)
        return GroupSlotSpotMarket(spot_market, maint_asset_weight, init_asset_weight, maint_liab_weight, init_liab_weight)

    @staticmethod
    def from_layout_or_none(layout: typing.Any) -> typing.Optional["GroupSlotSpotMarket"]:
        if (layout.spot_market is None) or (layout.spot_market == SYSTEM_PROGRAM_ADDRESS):
            return None

        return GroupSlotSpotMarket.from_layout(layout)

    def __str__(self) -> str:
        return f"""« 𝙶𝚛𝚘𝚞𝚙𝚂𝚕𝚘𝚝𝚂𝚙𝚘𝚝𝙼𝚊𝚛𝚔𝚎𝚝 [{self.address}]
    Asset Weights:
        Initial: {self.init_asset_weight}
        Maintenance: {self.maint_asset_weight}
    Liability Weights:
        Initial: {self.init_liab_weight}
        Maintenance: {self.maint_liab_weight}
»"""

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 GroupSlotPerpMarket class
#
class GroupSlotPerpMarket:
    def __init__(self, address: PublicKey, maint_asset_weight: Decimal, init_asset_weight: Decimal, maint_liab_weight: Decimal, init_liab_weight: Decimal, liquidation_fee: Decimal, base_lot_size: Decimal, quote_lot_size: Decimal) -> None:
        self.address: PublicKey = address
        self.maint_asset_weight: Decimal = maint_asset_weight
        self.init_asset_weight: Decimal = init_asset_weight
        self.maint_liab_weight: Decimal = maint_liab_weight
        self.init_liab_weight: Decimal = init_liab_weight
        self.liquidation_fee: Decimal = liquidation_fee
        self.base_lot_size: Decimal = base_lot_size
        self.quote_lot_size: Decimal = quote_lot_size

    @staticmethod
    def from_layout(layout: typing.Any) -> "GroupSlotPerpMarket":
        perp_market: PublicKey = layout.perp_market
        maint_asset_weight: Decimal = round(layout.maint_asset_weight, 8)
        init_asset_weight: Decimal = round(layout.init_asset_weight, 8)
        maint_liab_weight: Decimal = round(layout.maint_liab_weight, 8)
        init_liab_weight: Decimal = round(layout.init_liab_weight, 8)
        liquidation_fee: Decimal = round(layout.liquidation_fee, 8)
        base_lot_size: Decimal = layout.base_lot_size
        quote_lot_size: Decimal = layout.quote_lot_size

        return GroupSlotPerpMarket(perp_market, maint_asset_weight, init_asset_weight, maint_liab_weight, init_liab_weight, liquidation_fee, base_lot_size, quote_lot_size)

    @staticmethod
    def from_layout_or_none(layout: typing.Any) -> typing.Optional["GroupSlotPerpMarket"]:
        if (layout.perp_market is None) or (layout.perp_market == SYSTEM_PROGRAM_ADDRESS):
            return None

        return GroupSlotPerpMarket.from_layout(layout)

    def __str__(self) -> str:
        return f"""« 𝙶𝚛𝚘𝚞𝚙𝚂𝚕𝚘𝚝𝙿𝚎𝚛𝚙𝙼𝚊𝚛𝚔𝚎𝚝 [{self.address}]
    Asset Weights:
        Initial: {self.init_asset_weight}
        Maintenance: {self.maint_asset_weight}
    Liability Weights:
        Initial: {self.init_liab_weight}
        Maintenance: {self.maint_liab_weight}
    Liquidation Fee: {self.liquidation_fee}
    Base Lot Size: {self.base_lot_size}
    Quote Lot Size: {self.quote_lot_size}
»"""

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 GroupSlot class
#
# `GroupSlot` gathers indexed slot items together instead of separate arrays.
#
class GroupSlot:
    def __init__(self, base_instrument: Instrument, base_token_info: typing.Optional[TokenInfo], quote_token_info: TokenInfo, spot_market_info: typing.Optional[GroupSlotSpotMarket], perp_market_info: typing.Optional[GroupSlotPerpMarket], perp_lot_size_converter: LotSizeConverter, oracle: PublicKey) -> None:
        self.base_instrument: Instrument = base_instrument
        self.base_token_info: typing.Optional[TokenInfo] = base_token_info
        self.quote_token_info: TokenInfo = quote_token_info
        self.spot_market_info: typing.Optional[GroupSlotSpotMarket] = spot_market_info
        self.perp_market_info: typing.Optional[GroupSlotPerpMarket] = perp_market_info
        self.perp_lot_size_converter: LotSizeConverter = perp_lot_size_converter
        self.oracle: PublicKey = oracle

    def __str__(self) -> str:
        base_token_info = f"{self.base_token_info}".replace("\n", "\n        ")
        quote_token_info = f"{self.quote_token_info}".replace("\n", "\n        ")
        spot_market_info = f"{self.spot_market_info}".replace("\n", "\n        ")
        perp_market_info = f"{self.perp_market_info}".replace("\n", "\n        ")
        return f"""« 𝙶𝚛𝚘𝚞𝚙𝚂𝚕𝚘𝚝 {self.base_instrument}
    Base Token Info:
        {base_token_info}
    Quote Token Info:
        {quote_token_info}
    Oracle: {self.oracle}
    Spot Market:
        {spot_market_info}
    Perp Market:
        {perp_market_info}
»"""

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 Group class
#
# `Group` defines root functionality for Mango Markets.
#
class Group(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version, name: str,
                 meta_data: Metadata,
                 shared_quote: TokenInfo,
                 slot_indices: typing.Sequence[bool],
                 slots: typing.Sequence[GroupSlot],
                 signer_nonce: Decimal, signer_key: PublicKey,
                 admin: PublicKey, serum_program_address: PublicKey, cache: PublicKey, valid_interval: Decimal,
                 insurance_vault: PublicKey, srm_vault: PublicKey, msrm_vault: PublicKey, fees_vault: PublicKey) -> None:
        super().__init__(account_info)
        self.version: Version = version
        self.name: str = name

        self.meta_data: Metadata = meta_data
        self.shared_quote: TokenInfo = shared_quote
        self.slot_indices: typing.Sequence[bool] = slot_indices
        self.slots: typing.Sequence[GroupSlot] = slots
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
    def shared_quote_token(self) -> Token:
        return Token.ensure(self.shared_quote.token)

    @property
    def liquidity_incentive_token_info(self) -> TokenInfo:
        return self.find_token_info_by_symbol("MNGO")

    @property
    def liquidity_incentive_token(self) -> Token:
        return Token.ensure(self.liquidity_incentive_token_info.token)

    @property
    def tokens(self) -> typing.Sequence[TokenInfo]:
        return [*self.base_tokens, self.shared_quote]

    @property
    def tokens_by_index(self) -> typing.Sequence[typing.Optional[TokenInfo]]:
        return [*self.base_tokens_by_index, self.shared_quote]

    @property
    def slots_by_index(self) -> typing.Sequence[typing.Optional[GroupSlot]]:
        mapped_items: typing.List[typing.Optional[GroupSlot]] = []
        slot_counter = 0
        for available in self.slot_indices:
            if available:
                mapped_items += [self.slots[slot_counter]]
                slot_counter += 1
            else:
                mapped_items += [None]

        return mapped_items

    @property
    def base_tokens(self) -> typing.Sequence[TokenInfo]:
        return [slot.base_token_info for slot in self.slots if slot.base_token_info is not None]

    @property
    def base_tokens_by_index(self) -> typing.Sequence[typing.Optional[TokenInfo]]:
        return [slot.base_token_info if slot is not None else None for slot in self.slots_by_index]

    @property
    def oracles(self) -> typing.Sequence[PublicKey]:
        return [slot.oracle for slot in self.slots if slot.oracle is not None]

    @property
    def oracles_by_index(self) -> typing.Sequence[typing.Optional[PublicKey]]:
        return [slot.oracle if slot is not None else None for slot in self.slots_by_index]

    @property
    def spot_markets(self) -> typing.Sequence[GroupSlotSpotMarket]:
        return [slot.spot_market_info for slot in self.slots if slot.spot_market_info is not None]

    @property
    def spot_markets_by_index(self) -> typing.Sequence[typing.Optional[GroupSlotSpotMarket]]:
        return [slot.spot_market_info if slot is not None else None for slot in self.slots_by_index]

    @property
    def perp_markets(self) -> typing.Sequence[GroupSlotPerpMarket]:
        return [slot.perp_market_info for slot in self.slots if slot.perp_market_info is not None]

    @property
    def perp_markets_by_index(self) -> typing.Sequence[typing.Optional[GroupSlotPerpMarket]]:
        return [slot.perp_market_info if slot is not None else None for slot in self.slots_by_index]

    @staticmethod
    def from_layout(layout: typing.Any, name: str, account_info: AccountInfo, version: Version, root_banks: typing.Sequence[RootBank], instrument_lookup: InstrumentLookup, market_lookup: MarketLookup) -> "Group":
        meta_data: Metadata = Metadata.from_layout(layout.meta_data)
        tokens: typing.List[typing.Optional[TokenInfo]] = [
            TokenInfo.from_layout_or_none(t, instrument_lookup, root_banks) for t in layout.tokens]

        # By convention, the shared quote token is always at the end.
        quote_token_info: typing.Optional[TokenInfo] = tokens[-1]
        if quote_token_info is None:
            raise Exception("Could not find quote token info at end of group tokens.")
        slots: typing.List[GroupSlot] = []
        in_slots: typing.List[bool] = []
        for index in range(len(tokens) - 1):
            spot_market_info: typing.Optional[GroupSlotSpotMarket] = GroupSlotSpotMarket.from_layout_or_none(
                layout.spot_markets[index])
            perp_market_info: typing.Optional[GroupSlotPerpMarket] = GroupSlotPerpMarket.from_layout_or_none(
                layout.perp_markets[index])
            if (spot_market_info is None) and (perp_market_info is None):
                in_slots += [False]
            else:
                perp_lot_size_converter: LotSizeConverter = RaisingLotSizeConverter()
                base_token_info: typing.Optional[TokenInfo] = tokens[index]
                base_instrument: Instrument
                if base_token_info is not None:
                    base_instrument = base_token_info.token
                else:
                    # It's possible there's no underlying SPL token and we have a pure PERP market.
                    if perp_market_info is None:
                        raise Exception(f"Cannot find base token or perp market info for index {index}")
                    perp_market = market_lookup.find_by_address(perp_market_info.address)
                    if perp_market is None:
                        raise Exception(f"Cannot find base token or perp market for index {index}")
                    base_instrument = perp_market.base
                if perp_market_info is not None:
                    perp_lot_size_converter = LotSizeConverter(
                        base_instrument, perp_market_info.base_lot_size, quote_token_info.token, perp_market_info.quote_lot_size)

                oracle: PublicKey = layout.oracles[index]
                slot: GroupSlot = GroupSlot(
                    base_instrument, base_token_info, quote_token_info, spot_market_info, perp_market_info, perp_lot_size_converter, oracle)
                slots += [slot]
                in_slots += [True]

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

        return Group(account_info, version, name, meta_data, quote_token_info, in_slots, slots, signer_nonce, signer_key, admin, serum_program_address, cache, valid_interval, insurance_vault, srm_vault, msrm_vault, fees_vault)

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
        return Group.parse_locally(account_info, name, root_banks, context.instrument_lookup, context.market_lookup)

    @staticmethod
    def parse_locally(account_info: AccountInfo, name: str, root_banks: typing.Sequence[RootBank], instrument_lookup: InstrumentLookup, market_lookup: MarketLookup) -> "Group":
        data = account_info.data
        if len(data) != layouts.GROUP.sizeof():
            raise Exception(
                f"Group data length ({len(data)}) does not match expected size ({layouts.GROUP.sizeof()})")

        layout = layouts.GROUP.parse(data)
        return Group.from_layout(layout, name, account_info, Version.V3, root_banks, instrument_lookup, market_lookup)

    @staticmethod
    def load(context: Context, address: typing.Optional[PublicKey] = None) -> "Group":
        group_address: PublicKey = address or context.group_address
        account_info = AccountInfo.load(context, group_address)
        if account_info is None:
            raise Exception(f"Group account not found at address '{group_address}'")
        return Group.parse(context, account_info)

    def find_spot_market_index(self, spot_market_address: PublicKey) -> int:
        for index, spot in enumerate(self.spot_markets_by_index):
            if spot is not None and spot.address == spot_market_address:
                return index

        raise Exception(f"Could not find spot market {spot_market_address} in group {self.address}")

    def find_perp_market_index(self, perp_market_address: PublicKey) -> int:
        for index, pm in enumerate(self.perp_markets_by_index):
            if pm is not None and pm.address == perp_market_address:
                return index

        raise Exception(f"Could not find perp market {perp_market_address} in group {self.address}")

    def find_base_token_market_index(self, base_token: TokenInfo) -> int:
        for index, bt in enumerate(self.base_tokens_by_index):
            if bt is not None and bt.token == base_token.token:
                return index

        raise Exception(f"Could not find base token {base_token} in group {self.address}")

    def find_base_instrument_market_index(self, instrument: Instrument) -> int:
        for index, bt in enumerate(self.base_tokens_by_index):
            if bt is not None and bt.token == instrument:
                return index

        raise Exception(f"Could not find base instrument {instrument} in group {self.address}")

    def find_token_market_index_or_none(self, token: Instrument) -> typing.Optional[int]:
        for index, bt in enumerate(self.base_tokens_by_index):
            if bt is not None and bt.token == token:
                return index

        return None

    def find_token_market_index(self, token: Instrument) -> int:
        index = self.find_token_market_index_or_none(token)
        if index is not None:
            return index

        raise Exception(f"Could not find token {token} in group {self.address}")

    def find_token_info_by_token(self, instrument: Instrument) -> TokenInfo:
        for token_info in self.tokens:
            if token_info.token == instrument:
                return token_info

        raise Exception(f"Could not find token info for instrument {instrument} in group {self.address}")

    def find_token_info_by_symbol(self, symbol: str) -> TokenInfo:
        for token_info in self.tokens:
            if token_info.token.symbol_matches(symbol):
                return token_info

        raise Exception(f"Could not find token info for symbol '{symbol}' in group {self.address}")

    def token_price_from_cache(self, cache: Cache, token: Instrument) -> InstrumentValue:
        market_cache: MarketCache = self.market_cache_from_cache(cache, token)
        return market_cache.adjusted_price(token, self.shared_quote_token)

    def perp_market_cache_from_cache(self, cache: Cache, token: Instrument) -> typing.Optional[PerpMarketCache]:
        market_cache: MarketCache = self.market_cache_from_cache(cache, token)
        return market_cache.perp_market

    def market_cache_from_cache(self, cache: Cache, token: Instrument) -> MarketCache:
        token_index: int = self.find_token_market_index(token)
        return cache.market_cache_for_index(token_index)

    def __str__(self) -> str:
        slot_count = len(self.slots)
        slots = "\n        ".join([f"{item}".replace("\n", "\n        ") for item in self.slots])
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
    Basket [{slot_count} markets]:
        {slots}
»"""
