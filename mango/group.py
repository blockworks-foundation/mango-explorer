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

import logging
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
from .token import Instrument, Token
from .tokenbank import TokenBank
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
        return f"""« GroupSlotSpotMarket [{self.address}]
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
        return f"""« GroupSlotPerpMarket [{self.address}]
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
    def __init__(self, index: int, base_instrument: Instrument, base_token_bank: typing.Optional[TokenBank], quote_token_bank: TokenBank, spot_market_info: typing.Optional[GroupSlotSpotMarket], perp_market_info: typing.Optional[GroupSlotPerpMarket], perp_lot_size_converter: LotSizeConverter, oracle: PublicKey) -> None:
        self.index: int = index
        self.base_instrument: Instrument = base_instrument
        self.base_token_bank: typing.Optional[TokenBank] = base_token_bank
        self.quote_token_bank: TokenBank = quote_token_bank
        self.spot_market: typing.Optional[GroupSlotSpotMarket] = spot_market_info
        self.perp_market: typing.Optional[GroupSlotPerpMarket] = perp_market_info
        self.perp_lot_size_converter: LotSizeConverter = perp_lot_size_converter
        self.oracle: PublicKey = oracle

    def __str__(self) -> str:
        base_token_bank = f"{self.base_token_bank}".replace("\n", "\n        ")
        quote_token_bank = f"{self.quote_token_bank}".replace("\n", "\n        ")
        spot_market_info = f"{self.spot_market}".replace("\n", "\n        ")
        perp_market_info = f"{self.perp_market}".replace("\n", "\n        ")
        return f"""« GroupSlot[{self.index}] {self.base_instrument}
    Base Token Info:
        {base_token_bank}
    Quote Token Info:
        {quote_token_bank}
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
                 shared_quote: TokenBank,
                 slot_indices: typing.Sequence[bool],
                 slots: typing.Sequence[GroupSlot],
                 signer_nonce: Decimal, signer_key: PublicKey,
                 admin: PublicKey, serum_program_address: PublicKey, cache: PublicKey, valid_interval: Decimal,
                 insurance_vault: PublicKey, srm_vault: PublicKey, msrm_vault: PublicKey, fees_vault: PublicKey) -> None:
        super().__init__(account_info)
        self.version: Version = version
        self.name: str = name

        self.meta_data: Metadata = meta_data
        self.shared_quote: TokenBank = shared_quote
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
    def liquidity_incentive_token_bank(self) -> TokenBank:
        for token_bank in self.tokens:
            if token_bank.token.symbol_matches("MNGO"):
                return token_bank

        raise Exception(f"Could not find token info for symbol 'MNGO' in group {self.address}")

    @property
    def liquidity_incentive_token(self) -> Token:
        return Token.ensure(self.liquidity_incentive_token_bank.token)

    @property
    def tokens(self) -> typing.Sequence[TokenBank]:
        return [*self.base_tokens, self.shared_quote]

    @property
    def tokens_by_index(self) -> typing.Sequence[typing.Optional[TokenBank]]:
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
    def base_tokens(self) -> typing.Sequence[TokenBank]:
        return [slot.base_token_bank for slot in self.slots if slot.base_token_bank is not None]

    @property
    def base_tokens_by_index(self) -> typing.Sequence[typing.Optional[TokenBank]]:
        return [slot.base_token_bank if slot is not None else None for slot in self.slots_by_index]

    @property
    def oracles(self) -> typing.Sequence[PublicKey]:
        return [slot.oracle for slot in self.slots if slot.oracle is not None]

    @property
    def oracles_by_index(self) -> typing.Sequence[typing.Optional[PublicKey]]:
        return [slot.oracle if slot is not None else None for slot in self.slots_by_index]

    @property
    def spot_markets(self) -> typing.Sequence[GroupSlotSpotMarket]:
        return [slot.spot_market for slot in self.slots if slot.spot_market is not None]

    @property
    def spot_markets_by_index(self) -> typing.Sequence[typing.Optional[GroupSlotSpotMarket]]:
        return [slot.spot_market if slot is not None else None for slot in self.slots_by_index]

    @property
    def perp_markets(self) -> typing.Sequence[GroupSlotPerpMarket]:
        return [slot.perp_market for slot in self.slots if slot.perp_market is not None]

    @property
    def perp_markets_by_index(self) -> typing.Sequence[typing.Optional[GroupSlotPerpMarket]]:
        return [slot.perp_market if slot is not None else None for slot in self.slots_by_index]

    @staticmethod
    def from_layout(layout: typing.Any, name: str, account_info: AccountInfo, version: Version, instrument_lookup: InstrumentLookup, market_lookup: MarketLookup) -> "Group":
        meta_data: Metadata = Metadata.from_layout(layout.meta_data)
        tokens: typing.List[typing.Optional[TokenBank]] = [
            TokenBank.from_layout_or_none(t, instrument_lookup) for t in layout.tokens]

        # By convention, the shared quote token is always at the end.
        quote_token_bank: typing.Optional[TokenBank] = tokens[-1]
        if quote_token_bank is None:
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
                base_token_bank: typing.Optional[TokenBank] = tokens[index]
                base_instrument: Instrument
                if base_token_bank is not None:
                    base_instrument = base_token_bank.token
                else:
                    # It's possible there's no underlying SPL token and we have a pure PERP market.
                    if perp_market_info is None:
                        raise Exception(f"Cannot find base token or perp market info for index {index}")
                    perp_market = market_lookup.find_by_address(perp_market_info.address)
                    if perp_market is None:
                        logging.warning(f"Group cannot find base token or perp market for index {index}")
                    else:
                        base_instrument = perp_market.base
                if perp_market_info is not None:
                    perp_lot_size_converter = LotSizeConverter(
                        base_instrument, perp_market_info.base_lot_size, quote_token_bank.token, perp_market_info.quote_lot_size)

                oracle: PublicKey = layout.oracles[index]
                slot: GroupSlot = GroupSlot(index, base_instrument, base_token_bank, quote_token_bank,
                                            spot_market_info, perp_market_info, perp_lot_size_converter, oracle)
                slots += [slot]
                in_slots += [True]

        signer_nonce: Decimal = layout.signer_nonce
        signer_key: PublicKey = layout.signer_key
        admin: PublicKey = layout.admin
        serum_program_address: PublicKey = layout.serum_program_address
        cache_address: PublicKey = layout.cache
        valid_interval: Decimal = layout.valid_interval
        insurance_vault: PublicKey = layout.insurance_vault
        srm_vault: PublicKey = layout.srm_vault
        msrm_vault: PublicKey = layout.msrm_vault
        fees_vault: PublicKey = layout.fees_vault

        return Group(account_info, version, name, meta_data, quote_token_bank, in_slots, slots, signer_nonce, signer_key, admin, serum_program_address, cache_address, valid_interval, insurance_vault, srm_vault, msrm_vault, fees_vault)

    @staticmethod
    def parse(account_info: AccountInfo, name: str, instrument_lookup: InstrumentLookup, market_lookup: MarketLookup) -> "Group":
        data = account_info.data
        if len(data) != layouts.GROUP.sizeof():
            raise Exception(
                f"Group data length ({len(data)}) does not match expected size ({layouts.GROUP.sizeof()})")

        layout = layouts.GROUP.parse(data)
        return Group.from_layout(layout, name, account_info, Version.V3, instrument_lookup, market_lookup)

    @staticmethod
    def parse_with_context(context: Context, account_info: AccountInfo) -> "Group":
        name = context.lookup_group_name(account_info.address)
        return Group.parse(account_info, name, context.instrument_lookup, context.market_lookup)

    @staticmethod
    def load(context: Context, address: typing.Optional[PublicKey] = None) -> "Group":
        group_address: PublicKey = address or context.group_address
        account_info = AccountInfo.load(context, group_address)
        if account_info is None:
            raise Exception(f"Group account not found at address '{group_address}'")

        name = context.lookup_group_name(account_info.address)
        return Group.parse(account_info, name, context.instrument_lookup, context.market_lookup)

    def slot_by_spot_market_address(self, spot_market_address: PublicKey) -> GroupSlot:
        for slot in self.slots:
            if slot.spot_market is not None and slot.spot_market.address == spot_market_address:
                return slot

        raise Exception(f"Could not find spot market {spot_market_address} in group {self.address}")

    def slot_by_perp_market_address(self, perp_market_address: PublicKey) -> GroupSlot:
        for slot in self.slots:
            if slot.perp_market is not None and slot.perp_market.address == perp_market_address:
                return slot

        raise Exception(f"Could not find perp market {perp_market_address} in group {self.address}")

    def slot_by_instrument_or_none(self, instrument: Instrument) -> typing.Optional[GroupSlot]:
        for slot in self.slots:
            if slot.base_instrument == instrument:
                return slot

        return None

    def slot_by_instrument(self, instrument: Instrument) -> GroupSlot:
        slot: typing.Optional[GroupSlot] = self.slot_by_instrument_or_none(instrument)
        if slot is not None:
            return slot

        raise Exception(f"Could not find slot for {instrument} in group {self.address}")

    def token_bank_by_instrument(self, instrument: Instrument) -> TokenBank:
        for token_bank in self.tokens:
            if token_bank.token == instrument:
                return token_bank

        raise Exception(f"Could not find token {instrument} in group {self.address}")

    def token_price_from_cache(self, cache: Cache, token: Instrument) -> InstrumentValue:
        if token == self.shared_quote_token:
            # 1 USDC is always worth 1 USDC
            return InstrumentValue(self.shared_quote_token, Decimal(1))
        else:
            market_cache: MarketCache = self.market_cache_from_cache(cache, token)
            return market_cache.adjusted_price(token, self.shared_quote_token)

    def perp_market_cache_from_cache(self, cache: Cache, token: Instrument) -> typing.Optional[PerpMarketCache]:
        market_cache: MarketCache = self.market_cache_from_cache(cache, token)
        return market_cache.perp_market

    def market_cache_from_cache(self, cache: Cache, instrument: Instrument) -> MarketCache:
        slot: GroupSlot = self.slot_by_instrument(instrument)
        instrument_index: int = slot.index
        return cache.market_cache_for_index(instrument_index)

    def fetch_cache(self, context: Context) -> Cache:
        return Cache.load(context, self.cache)

    def __str__(self) -> str:
        slot_count = len(self.slots)
        slots = "\n        ".join([f"{item}".replace("\n", "\n        ") for item in self.slots])
        return f"""« Group {self.version} [{self.address}]
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
