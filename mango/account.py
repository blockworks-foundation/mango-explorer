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
from solana.rpc.types import MemcmpOpts

from .accountinfo import AccountInfo
from .addressableaccount import AddressableAccount
from .cache import Cache, RootBankCache
from .context import Context
from .encoding import encode_key
from .group import Group
from .instrumentvalue import InstrumentValue
from .layouts import layouts
from .metadata import Metadata
from .openorders import OpenOrders
from .orders import Side
from .perpaccount import PerpAccount
from .perpopenorders import PerpOpenOrders
from .placedorder import PlacedOrder
from .token import Instrument, Token
from .tokenbank import TokenBank
from .version import Version


# # 🥭 AccountSlot class
#
# `AccountSlot` gathers slot items together instead of separate arrays.
#
class AccountSlot:
    def __init__(self, index: int, base_instrument: Instrument, base_token_bank: typing.Optional[TokenBank], quote_token_bank: TokenBank, raw_deposit: Decimal, deposit: InstrumentValue, raw_borrow: Decimal, borrow: InstrumentValue, spot_open_orders: typing.Optional[PublicKey], perp_account: typing.Optional[PerpAccount]) -> None:
        self.index: int = index
        self.base_instrument: Instrument = base_instrument
        self.base_token_bank: typing.Optional[TokenBank] = base_token_bank
        self.quote_token_bank: TokenBank = quote_token_bank
        self.raw_deposit: Decimal = raw_deposit
        self.deposit: InstrumentValue = deposit
        self.raw_borrow: Decimal = raw_borrow
        self.borrow: InstrumentValue = borrow
        self.spot_open_orders: typing.Optional[PublicKey] = spot_open_orders
        self.perp_account: typing.Optional[PerpAccount] = perp_account

    @property
    def net_value(self) -> InstrumentValue:
        return self.deposit - self.borrow

    @property
    def raw_net_value(self) -> Decimal:
        return self.raw_deposit - self.raw_borrow

    def __str__(self) -> str:
        perp_account: str = "None"
        if self.perp_account is not None:
            perp_account = f"{self.perp_account}".replace("\n", "\n        ")
        return f"""« AccountSlot {self.base_instrument.symbol}
    Net Value:     {self.net_value}
        Deposited: {self.deposit} (raw value: {self.raw_deposit})
        Borrowed:  {self.borrow} (raw value {self.raw_borrow})
    Spot OpenOrders: {self.spot_open_orders or "None"}
    Perp Account:
        {perp_account}
»"""

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 Account class
#
# `Account` holds information about the account for a particular user/wallet for a particualr `Group`.
#
class Account(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version,
                 meta_data: Metadata, group_name: str, group_address: PublicKey, owner: PublicKey,
                 info: str, shared_quote: AccountSlot,
                 in_margin_basket: typing.Sequence[bool],
                 slot_indices: typing.Sequence[bool],
                 base_slots: typing.Sequence[AccountSlot],
                 msrm_amount: Decimal, being_liquidated: bool, is_bankrupt: bool) -> None:
        super().__init__(account_info)
        self.version: Version = version

        self.meta_data: Metadata = meta_data
        self.group_name: str = group_name
        self.group_address: PublicKey = group_address
        self.owner: PublicKey = owner
        self.info: str = info
        self.shared_quote: AccountSlot = shared_quote
        self.in_margin_basket: typing.Sequence[bool] = in_margin_basket
        self.slot_indices: typing.Sequence[bool] = slot_indices
        self.base_slots: typing.Sequence[AccountSlot] = base_slots
        self.msrm_amount: Decimal = msrm_amount
        self.being_liquidated: bool = being_liquidated
        self.is_bankrupt: bool = is_bankrupt

    @property
    def shared_quote_token(self) -> Token:
        token_bank = self.shared_quote.base_token_bank
        if token_bank is None:
            raise Exception(f"Shared quote does not have a token: {self.shared_quote}")
        return Token.ensure(token_bank.token)

    @property
    def slots(self) -> typing.Sequence[AccountSlot]:
        return [*[slot for slot in self.base_slots], self.shared_quote]

    @property
    def slots_by_index(self) -> typing.Sequence[typing.Optional[AccountSlot]]:
        mapped_items: typing.List[typing.Optional[AccountSlot]] = []
        slot_counter = 0
        for available in self.slot_indices:
            if available:
                mapped_items += [self.base_slots[slot_counter]]
                slot_counter += 1
            else:
                mapped_items += [None]
        mapped_items += [self.shared_quote]

        return mapped_items

    @property
    def deposits(self) -> typing.Sequence[InstrumentValue]:
        return [slot.deposit for slot in self.slots]

    @property
    def deposits_by_index(self) -> typing.Sequence[typing.Optional[InstrumentValue]]:
        return [slot.deposit if slot is not None else None for slot in self.slots_by_index]

    @property
    def borrows(self) -> typing.Sequence[InstrumentValue]:
        return [slot.borrow for slot in self.slots]

    @property
    def borrows_by_index(self) -> typing.Sequence[typing.Optional[InstrumentValue]]:
        return [slot.borrow if slot is not None else None for slot in self.slots_by_index]

    @property
    def net_values(self) -> typing.Sequence[InstrumentValue]:
        return [slot.net_value for slot in self.slots]

    @property
    def net_values_by_index(self) -> typing.Sequence[typing.Optional[InstrumentValue]]:
        return [slot.net_value if slot is not None else None for slot in self.slots_by_index]

    @property
    def spot_open_orders(self) -> typing.Sequence[PublicKey]:
        return [slot.spot_open_orders for slot in self.base_slots if slot.spot_open_orders is not None]

    @property
    def spot_open_orders_by_index(self) -> typing.Sequence[typing.Optional[PublicKey]]:
        return [slot.spot_open_orders if slot is not None else None for slot in self.slots_by_index]

    @property
    def perp_accounts(self) -> typing.Sequence[PerpAccount]:
        return [slot.perp_account for slot in self.base_slots if slot.perp_account is not None]

    @property
    def perp_accounts_by_index(self) -> typing.Sequence[typing.Optional[PerpAccount]]:
        return [slot.perp_account if slot is not None else None for slot in self.slots_by_index]

    @staticmethod
    def from_layout(layout: typing.Any, account_info: AccountInfo, version: Version, group: Group, cache: Cache) -> "Account":
        meta_data = Metadata.from_layout(layout.meta_data)
        owner: PublicKey = layout.owner
        info: str = layout.info
        mngo_token = group.liquidity_incentive_token
        in_margin_basket: typing.Sequence[bool] = list([bool(in_basket) for in_basket in layout.in_margin_basket])
        active_in_basket: typing.List[bool] = []
        slots: typing.List[AccountSlot] = []
        placed_orders_all_markets: typing.List[typing.List[PlacedOrder]] = [[]
                                                                            for _ in range(len(group.slot_indices) - 1)]
        for index, order_market in enumerate(layout.order_market):
            if order_market != 0xFF:
                side = Side.from_value(layout.order_side[index])
                id = layout.order_ids[index]
                client_id = layout.client_order_ids[index]
                placed_order = PlacedOrder(id, client_id, side)
                placed_orders_all_markets[int(order_market)] += [placed_order]

        quote_token_bank: TokenBank = group.shared_quote
        quote_token: Token = group.shared_quote_token

        for index in range(len(group.slots_by_index)):
            group_slot = group.slots_by_index[index]
            if group_slot is not None:
                instrument = group_slot.base_instrument
                token_bank = group_slot.base_token_bank
                raw_deposit: Decimal = Decimal(0)
                intrinsic_deposit: Decimal = Decimal(0)
                raw_borrow: Decimal = Decimal(0)
                intrinsic_borrow: Decimal = Decimal(0)
                if token_bank is not None:
                    raw_deposit = layout.deposits[index]
                    root_bank_cache: typing.Optional[RootBankCache] = token_bank.root_bank_cache_from_cache(
                        cache, index)
                    if root_bank_cache is None:
                        raise Exception(f"No root bank cache found for token {token_bank} at index {index}")
                    intrinsic_deposit = root_bank_cache.deposit_index * raw_deposit
                    raw_borrow = layout.borrows[index]
                    intrinsic_borrow = root_bank_cache.borrow_index * raw_borrow

                deposit = InstrumentValue(instrument, instrument.shift_to_decimals(intrinsic_deposit))
                borrow = InstrumentValue(instrument, instrument.shift_to_decimals(intrinsic_borrow))

                perp_open_orders = PerpOpenOrders(placed_orders_all_markets[index])

                perp_account = PerpAccount.from_layout(
                    layout.perp_accounts[index],
                    instrument,
                    quote_token,
                    perp_open_orders,
                    group_slot.perp_lot_size_converter,
                    mngo_token)
                spot_open_orders = layout.spot_open_orders[index]
                account_slot: AccountSlot = AccountSlot(index, instrument, token_bank, quote_token_bank,
                                                        raw_deposit, deposit, raw_borrow, borrow,
                                                        spot_open_orders, perp_account)

                slots += [account_slot]
                active_in_basket += [True]
            else:
                active_in_basket += [False]

        quote_index: int = len(layout.deposits) - 1
        raw_quote_deposit: Decimal = layout.deposits[quote_index]
        quote_root_bank_cache: typing.Optional[RootBankCache] = quote_token_bank.root_bank_cache_from_cache(
            cache, quote_index)
        if quote_root_bank_cache is None:
            raise Exception(f"No root bank cache found for quote token {quote_token_bank} at index {index}")
        intrinsic_quote_deposit = quote_root_bank_cache.deposit_index * raw_quote_deposit
        quote_deposit = InstrumentValue(quote_token, quote_token.shift_to_decimals(intrinsic_quote_deposit))
        raw_quote_borrow: Decimal = layout.borrows[quote_index]
        intrinsic_quote_borrow = quote_root_bank_cache.borrow_index * raw_quote_borrow
        quote_borrow = InstrumentValue(quote_token, quote_token.shift_to_decimals(intrinsic_quote_borrow))
        quote: AccountSlot = AccountSlot(len(layout.deposits) - 1, quote_token_bank.token, quote_token_bank,
                                         quote_token_bank, raw_quote_deposit, quote_deposit, raw_quote_borrow,
                                         quote_borrow, None, None)

        msrm_amount: Decimal = layout.msrm_amount
        being_liquidated: bool = bool(layout.being_liquidated)
        is_bankrupt: bool = bool(layout.is_bankrupt)

        return Account(account_info, version, meta_data, group.name, group.address, owner, info, quote, in_margin_basket, active_in_basket, slots, msrm_amount, being_liquidated, is_bankrupt)

    @staticmethod
    def parse(account_info: AccountInfo, group: Group, cache: Cache) -> "Account":
        data = account_info.data
        if len(data) != layouts.MANGO_ACCOUNT.sizeof():
            raise Exception(
                f"Account data length ({len(data)}) does not match expected size ({layouts.MANGO_ACCOUNT.sizeof()})")

        layout = layouts.MANGO_ACCOUNT.parse(data)
        return Account.from_layout(layout, account_info, Version.V3, group, cache)

    @staticmethod
    def load(context: Context, address: PublicKey, group: Group) -> "Account":
        account_info = AccountInfo.load(context, address)
        if account_info is None:
            raise Exception(f"Account account not found at address '{address}'")
        cache: Cache = group.fetch_cache(context)
        return Account.parse(account_info, group, cache)

    @staticmethod
    def load_all(context: Context, group: Group) -> typing.Sequence["Account"]:
        # mango_group is just after the METADATA, which is the first entry.
        group_offset = layouts.METADATA.sizeof()
        # owner is just after mango_group in the layout, and it's a PublicKey which is 32 bytes.
        filters = [
            MemcmpOpts(
                offset=group_offset,
                bytes=encode_key(group.address)
            )
        ]

        results = context.client.get_program_accounts(
            context.mango_program_address, memcmp_opts=filters, data_size=layouts.MANGO_ACCOUNT.sizeof())
        cache: Cache = group.fetch_cache(context)
        accounts: typing.List[Account] = []
        for account_data in results:
            address = PublicKey(account_data["pubkey"])
            account_info = AccountInfo._from_response_values(account_data["account"], address)
            account = Account.parse(account_info, group, cache)
            accounts += [account]
        return accounts

    @staticmethod
    def load_all_for_owner(context: Context, owner: PublicKey, group: Group) -> typing.Sequence["Account"]:
        # mango_group is just after the METADATA, which is the first entry.
        group_offset = layouts.METADATA.sizeof()
        # owner is just after mango_group in the layout, and it's a PublicKey which is 32 bytes.
        owner_offset = group_offset + 32
        filters = [
            MemcmpOpts(
                offset=group_offset,
                bytes=encode_key(group.address)
            ),
            MemcmpOpts(
                offset=owner_offset,
                bytes=encode_key(owner)
            )
        ]

        results = context.client.get_program_accounts(
            context.mango_program_address, memcmp_opts=filters, data_size=layouts.MANGO_ACCOUNT.sizeof())
        cache: Cache = group.fetch_cache(context)
        accounts: typing.List[Account] = []
        for account_data in results:
            address = PublicKey(account_data["pubkey"])
            account_info = AccountInfo._from_response_values(account_data["account"], address)
            account = Account.parse(account_info, group, cache)
            accounts += [account]
        return accounts

    @staticmethod
    def load_for_owner_by_address(context: Context, owner: PublicKey, group: Group, account_address: typing.Optional[PublicKey]) -> "Account":
        if account_address is not None:
            return Account.load(context, account_address, group)

        accounts: typing.Sequence[Account] = Account.load_all_for_owner(context, owner, group)
        if len(accounts) > 1:
            raise Exception(f"More than 1 Mango account for owner '{owner}' and which to choose not specified.")

        return accounts[0]

    def slot_by_instrument_or_none(self, instrument: Instrument) -> typing.Optional[AccountSlot]:
        for slot in self.slots:
            if slot.base_instrument == instrument:
                return slot

        return None

    def slot_by_instrument(self, instrument: Instrument) -> AccountSlot:
        slot: typing.Optional[AccountSlot] = self.slot_by_instrument_or_none(instrument)
        if slot is not None:
            return slot

        raise Exception(f"Could not find token {instrument} in account {self.address}")

    def load_all_spot_open_orders(self, context: Context) -> typing.Dict[str, OpenOrders]:
        spot_open_orders_account_infos = AccountInfo.load_multiple(context, self.spot_open_orders)
        spot_open_orders_account_infos_by_address = {
            str(account_info.address): account_info for account_info in spot_open_orders_account_infos}
        spot_open_orders: typing.Dict[str, OpenOrders] = {}
        for slot in self.base_slots:
            if slot.spot_open_orders is not None:
                account_info = spot_open_orders_account_infos_by_address[str(slot.spot_open_orders)]
                oo = OpenOrders.parse(account_info, slot.base_instrument.decimals,
                                      self.shared_quote.base_instrument.decimals)
                spot_open_orders[str(slot.spot_open_orders)] = oo
        return spot_open_orders

    def update_spot_open_orders_for_market(self, spot_market_index: int, spot_open_orders: PublicKey) -> None:
        item_to_update = self.slots_by_index[spot_market_index]
        if item_to_update is None:
            raise Exception(f"Could not find AccountBasketItem in Account {self.address} at index {spot_market_index}.")
        item_to_update.spot_open_orders = spot_open_orders

    def __str__(self) -> str:
        info = f"'{self.info}'" if self.info else "(un-named)"
        shared_quote: str = f"{self.shared_quote}".replace("\n", "\n        ")
        slot_count = len(self.base_slots)
        slots = "\n        ".join([f"{item}".replace("\n", "\n        ") for item in self.base_slots])

        symbols: typing.Sequence[str] = [slot.base_instrument.symbol for slot in self.base_slots]
        in_margin_basket = ", ".join(symbols) or "None"
        return f"""« Account {info}, {self.version} [{self.address}]
    {self.meta_data}
    Owner: {self.owner}
    Group: « Group '{self.group_name}' [{self.group_address}] »
    MSRM: {self.msrm_amount}
    Bankrupt? {self.is_bankrupt}
    Being Liquidated? {self.being_liquidated}
    Shared Quote Token:
        {shared_quote}
    In Basket: {in_margin_basket}
    Basket [{slot_count} in basket]:
        {slots}
»"""

    def __repr__(self) -> str:
        return f"{self}"
