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

import pandas
import typing

from dataclasses import dataclass
from decimal import Decimal
from solana.publickey import PublicKey
from solana.rpc.types import MemcmpOpts

from .accountinfo import AccountInfo
from .addressableaccount import AddressableAccount
from .cache import Cache, PerpMarketCache, RootBankCache, MarketCache
from .combinableinstructions import CombinableInstructions
from .constants import SYSTEM_PROGRAM_ADDRESS
from .context import Context
from .encoding import encode_key
from .group import Group, GroupSlot, GroupSlotPerpMarket
from .instructions import (
    build_mango_deposit_instructions,
    build_mango_settle_fees_instructions,
    build_mango_settle_pnl_instructions,
    build_mango_withdraw_instructions,
)
from .instrumentvalue import InstrumentValue
from .layouts import layouts
from .metadata import Metadata
from .observables import Disposable
from .openorders import OpenOrders
from .orders import Side
from .perpaccount import PerpAccount
from .perpmarketdetails import PerpMarketDetails
from .perpopenorders import PerpOpenOrders
from .placedorder import PlacedOrder
from .tokens import Instrument, Token
from .tokenaccount import TokenAccount
from .tokenbank import TokenBank
from .tokenoperations import build_create_associated_instructions_and_account
from .version import Version
from .wallet import Wallet
from .websocketsubscription import (
    WebSocketAccountSubscription,
    WebSocketSubscriptionManager,
)


# # 🥭 ReferrerMemory class
#
# `ReferrerMemory` stores the referrer's Mango Account address.
#
class ReferrerMemory(AddressableAccount):
    def __init__(
        self,
        account_info: AccountInfo,
        version: Version,
        meta_data: Metadata,
        referrer_mango_account: PublicKey,
    ) -> None:
        super().__init__(account_info)
        self.version: Version = version

        self.meta_data: Metadata = meta_data
        self.referrer_mango_account: PublicKey = referrer_mango_account

    @staticmethod
    def from_layout(
        layout: typing.Any, account_info: AccountInfo, version: Version
    ) -> "ReferrerMemory":
        meta_data: Metadata = Metadata.from_layout(layout.meta_data)
        referrer_mango_account: PublicKey = layout.referrer_mango_account

        return ReferrerMemory(account_info, version, meta_data, referrer_mango_account)

    @staticmethod
    def parse(account_info: AccountInfo) -> "ReferrerMemory":
        data = account_info.data
        if len(data) != layouts.REFERRER_MEMORY.sizeof():
            raise Exception(
                f"ReferrerMemory data length ({len(data)}) does not match expected size ({layouts.REFERRER_MEMORY.sizeof()})"
            )

        layout = layouts.REFERRER_MEMORY.parse(data)
        return ReferrerMemory.from_layout(layout, account_info, Version.V1)

    @staticmethod
    def load_or_none(
        context: Context, address: PublicKey
    ) -> typing.Optional["ReferrerMemory"]:
        account_info = AccountInfo.load(context, address)
        if account_info is None:
            return None
        return ReferrerMemory.parse(account_info)

    @staticmethod
    def load(context: Context, address: PublicKey) -> "ReferrerMemory":
        referrer_memory: typing.Optional[ReferrerMemory] = ReferrerMemory.load_or_none(
            context, address
        )
        if referrer_memory is None:
            raise Exception(f"ReferrerMemory account not found at address '{address}'")
        return referrer_memory

    def subscribe(
        self,
        context: Context,
        websocketmanager: WebSocketSubscriptionManager,
        callback: typing.Callable[["ReferrerMemory"], None],
    ) -> Disposable:
        subscription = WebSocketAccountSubscription(
            context, self.address, ReferrerMemory.parse
        )
        websocketmanager.add(subscription)
        subscription.publisher.subscribe(on_next=callback)  # type: ignore[call-arg]

        return subscription

    def __str__(self) -> str:
        return f"""« ReferrerMemory [{self.version}] {self.address}
    {self.meta_data}
    Referrer: {self.referrer_mango_account}
»"""


# # 🥭 AccountSlot class
#
# `AccountSlot` gathers slot items together instead of separate arrays.
#
class AccountSlot:
    def __init__(
        self,
        index: int,
        base_instrument: Instrument,
        base_token_bank: typing.Optional[TokenBank],
        quote_token_bank: TokenBank,
        raw_deposit: Decimal,
        deposit: InstrumentValue,
        raw_borrow: Decimal,
        borrow: InstrumentValue,
        spot_open_orders: typing.Optional[PublicKey],
        perp_account: typing.Optional[PerpAccount],
    ) -> None:
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

    def pnl(
        self,
        perp_market_cache: PerpMarketCache,
        price: InstrumentValue,
    ) -> Decimal:
        if self.perp_account is None:
            return Decimal(0)
        return self.perp_account.pnl(perp_market_cache, price)

    def __str__(self) -> str:
        perp_account: str = "None"
        if self.perp_account is not None:
            perp_account = f"{self.perp_account}".replace("\n", "\n        ")
        return f"""« AccountSlot [{self.index}] {self.base_instrument.symbol}
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
    @staticmethod
    def __sum_neg(dataframe: pandas.DataFrame, name: str) -> Decimal:
        return typing.cast(Decimal, dataframe.loc[dataframe[name] < 0, name].sum())

    @staticmethod
    def __sum_pos(dataframe: pandas.DataFrame, name: str) -> Decimal:
        return typing.cast(Decimal, dataframe.loc[dataframe[name] > 0, name].sum())

    def __init__(
        self,
        account_info: AccountInfo,
        version: Version,
        meta_data: Metadata,
        group_name: str,
        group_address: PublicKey,
        owner: PublicKey,
        info: str,
        shared_quote: AccountSlot,
        in_margin_basket: typing.Sequence[bool],
        slot_indices: typing.Sequence[bool],
        base_slots: typing.Sequence[AccountSlot],
        msrm_amount: Decimal,
        being_liquidated: bool,
        is_bankrupt: bool,
        advanced_orders: PublicKey,
        not_upgradable: bool,
        delegate: PublicKey,
    ) -> None:
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
        self.advanced_orders: PublicKey = advanced_orders
        self.not_upgradable: bool = not_upgradable
        self.delegate: PublicKey = delegate

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
    def base_slots_by_index(self) -> typing.Sequence[typing.Optional[AccountSlot]]:
        mapped_items: typing.List[typing.Optional[AccountSlot]] = []
        slot_counter = 0
        for available in self.slot_indices:
            if available:
                mapped_items += [self.base_slots[slot_counter]]
                slot_counter += 1
            else:
                mapped_items += [None]

        return mapped_items

    @property
    def slots_by_index(self) -> typing.Sequence[typing.Optional[AccountSlot]]:
        return [*self.base_slots_by_index, self.shared_quote]

    @property
    def deposits(self) -> typing.Sequence[InstrumentValue]:
        return [slot.deposit for slot in self.slots]

    @property
    def deposits_by_index(self) -> typing.Sequence[typing.Optional[InstrumentValue]]:
        return [
            slot.deposit if slot is not None else None for slot in self.slots_by_index
        ]

    @property
    def borrows(self) -> typing.Sequence[InstrumentValue]:
        return [slot.borrow for slot in self.slots]

    @property
    def borrows_by_index(self) -> typing.Sequence[typing.Optional[InstrumentValue]]:
        return [
            slot.borrow if slot is not None else None for slot in self.slots_by_index
        ]

    @property
    def net_values(self) -> typing.Sequence[InstrumentValue]:
        return [slot.net_value for slot in self.slots]

    @property
    def net_values_by_index(self) -> typing.Sequence[typing.Optional[InstrumentValue]]:
        return [
            slot.net_value if slot is not None else None for slot in self.slots_by_index
        ]

    @property
    def spot_open_orders(self) -> typing.Sequence[PublicKey]:
        return [
            slot.spot_open_orders
            for slot in self.base_slots
            if slot.spot_open_orders is not None
        ]

    @property
    def spot_open_orders_by_index(self) -> typing.Sequence[typing.Optional[PublicKey]]:
        return [
            slot.spot_open_orders if slot is not None else None
            for slot in self.base_slots_by_index
        ]

    @property
    def perp_accounts(self) -> typing.Sequence[PerpAccount]:
        return [
            slot.perp_account
            for slot in self.base_slots
            if slot.perp_account is not None
        ]

    @property
    def perp_accounts_by_index(self) -> typing.Sequence[typing.Optional[PerpAccount]]:
        return [
            slot.perp_account if slot is not None else None
            for slot in self.slots_by_index
        ]

    @staticmethod
    def from_layout(
        layout: typing.Any,
        account_info: AccountInfo,
        version: Version,
        group: Group,
        cache: Cache,
    ) -> "Account":
        meta_data = Metadata.from_layout(layout.meta_data)
        owner: PublicKey = layout.owner
        info: str = layout.info
        mngo_token = group.liquidity_incentive_token
        in_margin_basket: typing.Sequence[bool] = list(
            [bool(in_basket) for in_basket in layout.in_margin_basket]
        )
        active_in_basket: typing.List[bool] = []
        slots: typing.List[AccountSlot] = []
        placed_orders_all_markets: typing.List[typing.List[PlacedOrder]] = [
            [] for _ in range(len(group.slot_indices) - 1)
        ]
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
                    root_bank_cache: typing.Optional[
                        RootBankCache
                    ] = token_bank.root_bank_cache_from_cache(cache, index)
                    if root_bank_cache is None:
                        raise Exception(
                            f"No root bank cache found for token {token_bank} at index {index}"
                        )
                    intrinsic_deposit = root_bank_cache.deposit_index * raw_deposit
                    raw_borrow = layout.borrows[index]
                    intrinsic_borrow = root_bank_cache.borrow_index * raw_borrow

                deposit = InstrumentValue(
                    instrument, instrument.shift_to_decimals(intrinsic_deposit)
                )
                borrow = InstrumentValue(
                    instrument, instrument.shift_to_decimals(intrinsic_borrow)
                )

                perp_open_orders = PerpOpenOrders(placed_orders_all_markets[index])

                perp_account = PerpAccount.from_layout(
                    layout.perp_accounts[index],
                    instrument,
                    quote_token,
                    perp_open_orders,
                    group_slot.perp_lot_size_converter,
                    mngo_token,
                )
                spot_open_orders = layout.spot_open_orders[index]
                account_slot: AccountSlot = AccountSlot(
                    index,
                    instrument,
                    token_bank,
                    quote_token_bank,
                    raw_deposit,
                    deposit,
                    raw_borrow,
                    borrow,
                    spot_open_orders,
                    perp_account,
                )

                slots += [account_slot]
                active_in_basket += [True]
            else:
                active_in_basket += [False]

        quote_index: int = len(layout.deposits) - 1
        raw_quote_deposit: Decimal = layout.deposits[quote_index]
        quote_root_bank_cache: typing.Optional[
            RootBankCache
        ] = quote_token_bank.root_bank_cache_from_cache(cache, quote_index)
        if quote_root_bank_cache is None:
            raise Exception(
                f"No root bank cache found for quote token {quote_token_bank} at index {index}"
            )
        intrinsic_quote_deposit = (
            quote_root_bank_cache.deposit_index * raw_quote_deposit
        )
        quote_deposit = InstrumentValue(
            quote_token, quote_token.shift_to_decimals(intrinsic_quote_deposit)
        )
        raw_quote_borrow: Decimal = layout.borrows[quote_index]
        intrinsic_quote_borrow = quote_root_bank_cache.borrow_index * raw_quote_borrow
        quote_borrow = InstrumentValue(
            quote_token, quote_token.shift_to_decimals(intrinsic_quote_borrow)
        )
        quote: AccountSlot = AccountSlot(
            len(layout.deposits) - 1,
            quote_token_bank.token,
            quote_token_bank,
            quote_token_bank,
            raw_quote_deposit,
            quote_deposit,
            raw_quote_borrow,
            quote_borrow,
            None,
            None,
        )

        msrm_amount: Decimal = layout.msrm_amount
        being_liquidated: bool = bool(layout.being_liquidated)
        is_bankrupt: bool = bool(layout.is_bankrupt)
        advanced_orders: PublicKey = layout.advanced_orders
        not_upgradable: bool = bool(layout.not_upgradable)
        delegate: PublicKey = layout.delegate

        return Account(
            account_info,
            version,
            meta_data,
            group.name,
            group.address,
            owner,
            info,
            quote,
            in_margin_basket,
            active_in_basket,
            slots,
            msrm_amount,
            being_liquidated,
            is_bankrupt,
            advanced_orders,
            not_upgradable,
            delegate,
        )

    @staticmethod
    def parse(account_info: AccountInfo, group: Group, cache: Cache) -> "Account":
        data = account_info.data
        if len(data) != layouts.MANGO_ACCOUNT.sizeof():
            raise Exception(
                f"Account data length ({len(data)}) does not match expected size ({layouts.MANGO_ACCOUNT.sizeof()})"
            )

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
        filters = [MemcmpOpts(offset=group_offset, bytes=encode_key(group.address))]

        account_infos = AccountInfo.load_by_program(
            context,
            context.mango_program_address,
            memcmp_opts=filters,
            data_size=layouts.MANGO_ACCOUNT.sizeof(),
        )
        cache: Cache = group.fetch_cache(context)
        accounts: typing.List[Account] = []
        for account_info in account_infos:
            account = Account.parse(account_info, group, cache)
            accounts += [account]
        return accounts

    @staticmethod
    def load_all_for_owner(
        context: Context, owner: PublicKey, group: Group
    ) -> typing.Sequence["Account"]:
        # mango_group is just after the METADATA, which is the first entry.
        group_offset = layouts.METADATA.sizeof()
        # owner is just after mango_group in the layout, and it's a PublicKey which is 32 bytes.
        owner_offset = group_offset + 32
        filters = [
            MemcmpOpts(offset=group_offset, bytes=encode_key(group.address)),
            MemcmpOpts(offset=owner_offset, bytes=encode_key(owner)),
        ]

        account_infos = AccountInfo.load_by_program(
            context,
            context.mango_program_address,
            memcmp_opts=filters,
            data_size=layouts.MANGO_ACCOUNT.sizeof(),
        )
        cache: Cache = group.fetch_cache(context)
        accounts: typing.List[Account] = []
        for account_info in account_infos:
            account = Account.parse(account_info, group, cache)
            accounts += [account]
        return accounts

    @staticmethod
    def load_all_for_delegate(
        context: Context, delegate: PublicKey, group: Group
    ) -> typing.Sequence["Account"]:
        # mango_group is just after the METADATA, which is the first entry.
        group_offset = layouts.METADATA.sizeof()
        # delegate is a PublicKey which is 32 bytes that ends 5 bytes before the end of the layout
        delegate_offset = layouts.MANGO_ACCOUNT.sizeof() - 37
        filters = [
            MemcmpOpts(offset=group_offset, bytes=encode_key(group.address)),
            MemcmpOpts(offset=delegate_offset, bytes=encode_key(delegate)),
        ]

        account_infos = AccountInfo.load_by_program(
            context,
            context.mango_program_address,
            memcmp_opts=filters,
            data_size=layouts.MANGO_ACCOUNT.sizeof(),
        )
        cache: Cache = group.fetch_cache(context)
        accounts: typing.List[Account] = []
        for account_info in account_infos:
            account = Account.parse(account_info, group, cache)
            accounts += [account]
        return accounts

    @staticmethod
    def load_for_owner_by_address(
        context: Context,
        owner: PublicKey,
        group: Group,
        account_address: typing.Optional[PublicKey],
    ) -> "Account":
        if account_address is not None:
            return Account.load(context, account_address, group)

        accounts: typing.Sequence[Account] = Account.load_all_for_owner(
            context, owner, group
        )
        if len(accounts) > 1:
            raise Exception(
                f"More than 1 Mango account for owner '{owner}' and which to choose not specified."
            )

        return accounts[0]

    def subscribe(
        self,
        context: Context,
        websocketmanager: WebSocketSubscriptionManager,
        callback: typing.Callable[["Account"], None],
    ) -> Disposable:
        group: Group = Group.load(context, self.group_address)
        cache: Cache = group.fetch_cache(context)

        def __parser(account_info: AccountInfo) -> Account:
            return Account.parse(account_info, group, cache)

        subscription = WebSocketAccountSubscription(context, self.address, __parser)
        websocketmanager.add(subscription)
        subscription.publisher.subscribe(on_next=callback)  # type: ignore[call-arg]

        return subscription

    def deposit(
        self, context: Context, wallet: Wallet, value: InstrumentValue
    ) -> typing.Sequence[str]:
        token: Token = Token.ensure(value.token)
        token_account = TokenAccount.fetch_largest_for_owner_and_token(
            context, wallet.keypair.public_key, token
        )

        if token_account is None:
            raise Exception(
                f"Could not find token account for token {value.token} with owner {wallet.keypair}."
            )

        deposit_token_account = TokenAccount(
            token_account.account_info,
            token_account.version,
            token_account.owner,
            value,
        )

        group = Group.load(context, self.group_address)
        token_bank = group.token_bank_by_instrument(token)
        root_bank = token_bank.ensure_root_bank(context)
        node_bank = root_bank.pick_node_bank(context)

        signers: CombinableInstructions = CombinableInstructions.from_wallet(wallet)
        deposit = build_mango_deposit_instructions(
            context, wallet, group, self, root_bank, node_bank, deposit_token_account
        )

        all_instructions = signers + deposit
        return all_instructions.execute(context)

    def withdraw(
        self,
        context: Context,
        wallet: Wallet,
        destination: PublicKey,
        value: InstrumentValue,
        allow_borrow: bool,
    ) -> typing.Sequence[str]:
        destination_info: typing.Optional[AccountInfo] = AccountInfo.load(
            context, destination
        )
        if destination_info is None:
            raise Exception(f"Could not find wallet at address {destination}.")

        if destination_info.owner != SYSTEM_PROGRAM_ADDRESS:
            # This is not a root wallet account
            raise Exception(
                f"Can't withdraw to address {destination} - not a wallet address."
            )

        token: Token = Token.ensure(value.token)
        token_account = TokenAccount.fetch_largest_for_owner_and_token(
            context, destination, token
        )

        withdrawal_token_account: TokenAccount
        create_ata = CombinableInstructions.empty()
        if token_account is None:
            (
                create_ata,
                token_account,
            ) = build_create_associated_instructions_and_account(
                context, wallet, destination, token
            )

        withdrawal_token_account = TokenAccount(
            token_account.account_info,
            token_account.version,
            token_account.owner,
            value,
        )

        group = Group.load(context, self.group_address)
        token_bank = group.token_bank_by_instrument(token)
        root_bank = token_bank.ensure_root_bank(context)
        node_bank = root_bank.pick_node_bank(context)

        signers: CombinableInstructions = CombinableInstructions.from_wallet(wallet)
        withdraw = build_mango_withdraw_instructions(
            context,
            wallet,
            group,
            self,
            root_bank,
            node_bank,
            withdrawal_token_account,
            allow_borrow,
        )

        all_instructions = signers + create_ata + withdraw
        return all_instructions.execute(context)

    def redeem_all_perp_pnl(
        self,
        context: Context,
        wallet: Wallet,
        group: Group,
        cache: Cache,
    ) -> typing.Sequence[str]:
        all_accounts = Account.load_all(context, group)
        self._logger.debug(f"Fetched {len(all_accounts)} Mango Accounts.")

        instructions = CombinableInstructions.from_wallet(wallet)
        for slot in self.slots:
            if (slot.perp_account is not None) and (not slot.perp_account.empty):
                self._logger.debug(
                    f"Redeeming perp account for {slot.base_instrument.symbol}"
                )
                price = group.token_price_from_cache(cache, slot.base_instrument)
                perp_market_cache = group.perp_market_cache_from_cache(
                    cache, slot.base_instrument
                )
                if perp_market_cache is None:
                    raise Exception(
                        f"Could not load perp market cache for {slot.base_instrument.symbol} despite having a perp account for it."
                    )

                instructions += self.build_redeem_pnl_instructions_for_market(
                    context, group, all_accounts, slot, perp_market_cache, price
                )
            else:
                self._logger.debug(f"No perp account for {slot.base_instrument.symbol}")

        self._logger.debug(
            f"Have {len(instructions.instructions)} instructions to send for all perp markets."
        )

        return instructions.execute(context)

    def redeem_pnl_for_perp_market(
        self,
        context: Context,
        wallet: Wallet,
        group: Group,
        slot: AccountSlot,
        perp_market_cache: PerpMarketCache,
        price: InstrumentValue,
    ) -> typing.Sequence[str]:
        group_slot = group.slots[slot.index]
        if group_slot.perp_market is None:
            return []

        if slot.perp_account is None:
            return []

        pnl = slot.perp_account.pnl(perp_market_cache, price)
        if pnl == 0:
            # No PnL to redeem
            return []

        self._logger.debug(
            f"Trying to settle {pnl:,.8f} {group_slot.quote_token_bank.token.symbol}."
        )

        instructions = CombinableInstructions.from_wallet(wallet)

        all_accounts = Account.load_all(context, group)
        self._logger.debug(f"Fetched {len(all_accounts)} Mango Accounts.")

        instructions += self.build_redeem_pnl_instructions_for_market(
            context, group, all_accounts, slot, perp_market_cache, price
        )

        return instructions.execute(context)

    def build_redeem_pnl_instructions_for_market(
        self,
        context: Context,
        group: Group,
        all_accounts: typing.Sequence["Account"],
        slot: AccountSlot,
        perp_market_cache: PerpMarketCache,
        price: InstrumentValue,
    ) -> CombinableInstructions:
        group_slot = group.slots[slot.index]
        if group_slot.perp_market is None:
            self._logger.debug(f"No perp market for {slot.base_instrument.symbol}")
            return CombinableInstructions.empty()

        if slot.perp_account is None:
            self._logger.debug(f"No perp account for {slot.base_instrument.symbol}")
            return CombinableInstructions.empty()

        pnl = slot.perp_account.pnl(perp_market_cache, price)
        if pnl == 0:
            # No PnL to redeem
            return CombinableInstructions.empty()

        self._logger.debug(
            f"Trying to settle {pnl:,.8f} {group_slot.quote_token_bank.token.symbol} on {group_slot.perp_market_symbol}."
        )

        pnl_is_negative: bool = False
        if pnl < 0:
            pnl_is_negative = True

        quote_root_bank = group.shared_quote.ensure_root_bank(context)

        instructions = CombinableInstructions.empty()

        # If negative, build settle fees instruction
        if pnl_is_negative:
            perp_market = PerpMarketDetails.load(
                context, group_slot.perp_market.address, group
            )
            quote_node_bank = quote_root_bank.pick_node_bank(context)
            self._logger.debug("Adding SettleFees instruction.")
            instructions += build_mango_settle_fees_instructions(
                context,
                group,
                perp_market,
                self,
                quote_root_bank,
                quote_node_bank,
            )

        all_accounts_except_self = filter(
            lambda acc: acc.address != self.address,
            all_accounts,
        )

        # Filter out all accounts with zero or same-signed PnL
        if pnl_is_negative:
            filtered = list(
                filter(
                    lambda acc: acc.slots[slot.index].pnl(perp_market_cache, price) > 0,
                    all_accounts_except_self,
                )
            )
        else:
            filtered = list(
                filter(
                    lambda acc: acc.slots[slot.index].pnl(perp_market_cache, price) < 0,
                    all_accounts_except_self,
                )
            )
        self._logger.debug(
            f"Removed irrelevent accounts - now have {len(filtered)} Mango Accounts."
        )

        # Now we have a filtered list, sort it
        sorted_accounts = sorted(
            filtered,
            key=lambda acc: acc.slots[slot.index].pnl(perp_market_cache, price),
            reverse=pnl_is_negative,
        )

        # Add 5% to our collection so we're sure we're sending enough accounts even if
        # the price has shifted. (This doesn't affect the redemption value.)
        target_pnl = (pnl * Decimal("1.01")).copy_abs()

        # Loop over top N accounts until we have redeemed enough or we run out of accounts.
        collected = Decimal(0)
        for other in sorted_accounts:
            other_perp_account = other.slots[slot.index].perp_account
            if other_perp_account is not None:
                other_pnl = other_perp_account.pnl(perp_market_cache, price)

                # Build instruction
                instructions += build_mango_settle_pnl_instructions(
                    context,
                    group,
                    group_slot,
                    self,
                    other,
                    quote_root_bank,
                )

                collected += other_pnl
                self._logger.debug(
                    f"Collected {collected:,.8f} out of {target_pnl:,.8f} - added {other_pnl:,.8f} from {other.address}"
                )

                # Add 1% to our collection so we're sure we're sending enough accounts even if
                # the price has shifted. (This doesn't affect the redemption value.)
                if collected.copy_abs() > target_pnl:
                    self._logger.debug(
                        f"Done. Have collected {collected:,.8f} to redeem against."
                    )
                    break

        self._logger.debug(
            f"Have {len(instructions.instructions)} instructions to send for {group_slot.perp_market_symbol}."
        )

        return instructions

    def slot_by_instrument_or_none(
        self, instrument: Instrument
    ) -> typing.Optional[AccountSlot]:
        for slot in self.slots:
            if slot.base_instrument == instrument:
                return slot

        return None

    def slot_by_instrument(self, instrument: Instrument) -> AccountSlot:
        slot: typing.Optional[AccountSlot] = self.slot_by_instrument_or_none(instrument)
        if slot is not None:
            return slot

        raise Exception(f"Could not find token {instrument} in account {self.address}")

    def slot_by_spot_open_orders_or_none(
        self, spot_open_orders: PublicKey
    ) -> typing.Optional[AccountSlot]:
        for slot in self.slots:
            if slot.spot_open_orders == spot_open_orders:
                return slot

        return None

    def slot_by_spot_open_orders(self, spot_open_orders: PublicKey) -> AccountSlot:
        slot: typing.Optional[AccountSlot] = self.slot_by_spot_open_orders_or_none(
            spot_open_orders
        )
        if slot is not None:
            return slot

        raise Exception(
            f"Could not find spot open orders {spot_open_orders} in account {self.address}"
        )

    def load_all_spot_open_orders(
        self, context: Context
    ) -> typing.Dict[str, OpenOrders]:
        spot_open_orders_account_infos = AccountInfo.load_multiple(
            context, self.spot_open_orders
        )
        spot_open_orders_account_infos_by_address = {
            str(account_info.address): account_info
            for account_info in spot_open_orders_account_infos
        }
        spot_open_orders: typing.Dict[str, OpenOrders] = {}
        for slot in self.base_slots:
            if slot.spot_open_orders is not None:
                account_info = spot_open_orders_account_infos_by_address[
                    str(slot.spot_open_orders)
                ]
                oo = OpenOrders.parse(
                    account_info,
                    Token.ensure(slot.base_instrument),
                    Token.ensure(self.shared_quote.base_instrument),
                )
                spot_open_orders[str(slot.spot_open_orders)] = oo
        return spot_open_orders

    def update_spot_open_orders_for_market(
        self, spot_market_index: int, spot_open_orders: PublicKey
    ) -> None:
        item_to_update = self.slots_by_index[spot_market_index]
        if item_to_update is None:
            raise Exception(
                f"Could not find AccountBasketItem in Account {self.address} at index {spot_market_index}."
            )
        item_to_update.spot_open_orders = spot_open_orders

    def derive_referrer_memory_address(self, context: Context) -> PublicKey:
        referrer_memory_address_and_nonce: typing.Tuple[
            PublicKey, int
        ] = PublicKey.find_program_address(
            [bytes(self.address), b"ReferrerMemory"], context.mango_program_address
        )

        return referrer_memory_address_and_nonce[0]

    def fetch_default_referrer(
        self, context: Context
    ) -> typing.Optional[ReferrerMemory]:
        referrer_memory_address: PublicKey = self.derive_referrer_memory_address(
            context
        )
        return ReferrerMemory.load_or_none(context, referrer_memory_address)

    def to_dataframe(
        self,
        group: Group,
        all_spot_open_orders: typing.Dict[str, OpenOrders],
        cache: Cache,
    ) -> pandas.DataFrame:
        asset_data = []
        for slot in self.slots:
            market_cache: typing.Optional[
                MarketCache
            ] = group.market_cache_from_cache_or_none(cache, slot.base_instrument)
            price: InstrumentValue = group.token_price_from_cache(
                cache, slot.base_instrument
            )

            spot_open_orders: typing.Optional[OpenOrders] = None
            spot_health_base: Decimal = slot.net_value.value
            spot_health_quote: Decimal = Decimal(0)
            spot_bids_base_net: Decimal = Decimal(0)
            spot_asks_base_net: Decimal = Decimal(0)
            if slot.spot_open_orders is not None:
                spot_open_orders = all_spot_open_orders[str(slot.spot_open_orders)]
                if spot_open_orders is None:
                    raise Exception(
                        f"OpenOrders address {slot.spot_open_orders} at index {slot.index} not loaded."
                    )

                # Here's a comment from ckamm in https://github.com/blockworks-foundation/mango-v3/pull/78/files
                # that describes some of the health calculations.
                #
                # // Two "worst-case" scenarios are considered:
                # // 1. All bids are executed at current price, producing a base amount of bids_base_net
                # //    when all quote_locked are converted to base.
                # // 2. All asks are executed at current price, producing a base amount of asks_base_net
                # //    because base_locked would be converted to quote.
                #
                # // Report the scenario that would have a worse outcome on health.
                # //
                # // Explanation: This function returns (base, quote) and the values later get used in
                # //     health += (if base > 0 { asset_weight } else { liab_weight }) * base + quote
                # // and here we return the scenario that will increase health the least.
                # //
                # // Correctness proof:
                # // - always bids_base_net >= asks_base_net
                # // - note that scenario 1 returns (a + b, c)
                # //         and scenario 2 returns (a,     c + b), and b >= 0, c >= 0
                # // - if a >= 0: scenario 1 will lead to less health as asset_weight <= 1.
                # // - if a < 0 and b <= -a: scenario 2 will lead to less health as liab_weight >= 1.
                # // - if a < 0 and b > -a:
                # //   The health contributions of both scenarios are identical if
                # //       asset_weight * (a + b) + c = liab_weight * a + c + b
                # //   <=> b = (asset_weight - liab_weight) / (1 - asset_weight) * a
                # //   <=> b = -2 a  since asset_weight + liab_weight = 2 by weight construction
                # //   So the worse scenario switches when a + b = -a.
                # // That means scenario 1 leads to less health whenever |a + b| > |a|.

                # base total if all bids were executed
                spot_bids_base_net = (
                    slot.net_value.value
                    + (spot_open_orders.quote_token_locked / price.value)
                    + spot_open_orders.base_token_total
                )

                # base total if all asks were executed
                spot_asks_base_net = (
                    slot.net_value.value + spot_open_orders.base_token_free
                )

                if spot_bids_base_net.copy_abs() > spot_asks_base_net.copy_abs():
                    spot_health_base = spot_bids_base_net
                    spot_health_quote = spot_open_orders.quote_token_free
                else:
                    spot_health_base = spot_asks_base_net
                    spot_health_quote = (
                        spot_open_orders.base_token_locked * price.value
                    ) + spot_open_orders.quote_token_total

            # From Daffy in Discord 2021-11-23: https://discord.com/channels/791995070613159966/857699200279773204/912705017767677982
            # --
            # There's a long_funding field on the PerpMarketCache which holds the current native USDC per
            # base position accrued. The long_settled_funding stores the last time funding was settled for
            # this particular user. So the funding owed is
            #   (PerpMarketCache.long_funding - PerpAccount.long_settled_funding) * PerpAccount.base_position
            # if base position greater than 0 (i.e. long)
            #
            # And we use short_funding if base_position < 0
            #
            # The long_funding field in PerpMarketCache changes across time according to the
            # update_funding() function. If orderbook is above index price, then long_funding and
            # short_funding both increase.
            #
            # Usually long_funding and short_funding will be the same unless there was a socialized loss
            # event. IF you have negative equity and insurance fund is empty, then half of the negative
            # equity goes to longs and half goes to shorts. The way that's done is by increasing
            # long_funding and decreasing short_funding by same amount.
            #
            # But unless there's a socialized loss, long_funding == short_funding
            # --
            perp_position: Decimal = Decimal(0)
            perp_notional_position: Decimal = Decimal(0)
            perp_health_base: Decimal = Decimal(0)
            perp_health_quote: Decimal = Decimal(0)
            unsettled_funding: Decimal = Decimal(0)
            perp_health_base_value: Decimal = Decimal(0)
            perp_asset: Decimal = Decimal(0)
            perp_liability: Decimal = Decimal(0)
            redeemable_pnl: Decimal = Decimal(0)
            perp_base_lot_size: Decimal = Decimal(0)
            perp_quote_lot_size: Decimal = Decimal(0)
            if (
                slot.perp_account is not None
                and not slot.perp_account.empty
                and market_cache is not None
            ):
                perp_market: typing.Optional[
                    GroupSlotPerpMarket
                ] = group.perp_markets_by_index[slot.index]
                if perp_market is None:
                    raise Exception(
                        f"Could not find perp market in Group at index {slot.index}."
                    )

                perp_base_lot_size = perp_market.base_lot_size
                perp_quote_lot_size = perp_market.quote_lot_size

                perp_position = (
                    slot.perp_account.lot_size_converter.base_size_lots_to_number(
                        slot.perp_account.base_position
                    )
                )
                perp_notional_position = perp_position * price.value
                cached_perp_market: typing.Optional[
                    PerpMarketCache
                ] = market_cache.perp_market
                if cached_perp_market is None:
                    raise Exception(
                        f"Could not find perp market in Cache at index {slot.index}."
                    )

                unsettled_funding = slot.perp_account.unsettled_funding(
                    cached_perp_market
                )
                bids_quantity = (
                    slot.perp_account.lot_size_converter.base_size_lots_to_number(
                        slot.perp_account.bids_quantity
                    )
                )
                asks_quantity = (
                    slot.perp_account.lot_size_converter.base_size_lots_to_number(
                        slot.perp_account.asks_quantity
                    )
                )
                taker_quote = (
                    slot.perp_account.lot_size_converter.quote_size_lots_to_number(
                        slot.perp_account.taker_quote
                    )
                )

                perp_bids_base_net: Decimal = perp_position + bids_quantity
                perp_asks_base_net: Decimal = perp_position - asks_quantity

                quote_pos = slot.perp_account.quote_position / (
                    10**self.shared_quote_token.decimals
                )
                if perp_bids_base_net.copy_abs() > perp_asks_base_net.copy_abs():
                    perp_health_base = perp_bids_base_net
                    perp_health_quote = (
                        (quote_pos + unsettled_funding)
                        + taker_quote
                        - (bids_quantity * price.value)
                    )
                else:
                    perp_health_base = perp_asks_base_net
                    perp_health_quote = (
                        (quote_pos + unsettled_funding)
                        + taker_quote
                        + (asks_quantity * price.value)
                    )
                perp_health_base_value = perp_health_base * price.value

                perp_asset = slot.perp_account.asset_value(
                    cached_perp_market, price.value
                )
                perp_liability = slot.perp_account.liability_value(
                    cached_perp_market, price.value
                )

                redeemable_pnl = slot.perp_account.pnl(cached_perp_market, price)

            group_slot: typing.Optional[GroupSlot] = None
            if market_cache is not None:
                group_slot = group.slot_by_instrument(slot.base_instrument)

            spot_init_asset_weight: Decimal = Decimal(0)
            spot_maint_asset_weight: Decimal = Decimal(0)
            spot_init_liab_weight: Decimal = Decimal(0)
            spot_maint_liab_weight: Decimal = Decimal(0)
            if group_slot is not None and group_slot.spot_market is not None:
                spot_init_asset_weight = group_slot.spot_market.init_asset_weight
                spot_maint_asset_weight = group_slot.spot_market.maint_asset_weight
                spot_init_liab_weight = group_slot.spot_market.init_liab_weight
                spot_maint_liab_weight = group_slot.spot_market.maint_liab_weight
            elif slot.base_instrument == self.shared_quote_token:
                spot_init_asset_weight = Decimal(1)
                spot_maint_asset_weight = Decimal(1)
                spot_init_liab_weight = Decimal(1)
                spot_maint_liab_weight = Decimal(1)

            perp_init_asset_weight: Decimal = Decimal(0)
            perp_maint_asset_weight: Decimal = Decimal(0)
            perp_init_liab_weight: Decimal = Decimal(0)
            perp_maint_liab_weight: Decimal = Decimal(0)
            if group_slot is not None and group_slot.perp_market is not None:
                perp_init_asset_weight = group_slot.perp_market.init_asset_weight
                perp_maint_asset_weight = group_slot.perp_market.maint_asset_weight
                perp_init_liab_weight = group_slot.perp_market.init_liab_weight
                perp_maint_liab_weight = group_slot.perp_market.maint_liab_weight
            elif slot.base_instrument == self.shared_quote_token:
                perp_init_asset_weight = Decimal(1)
                perp_maint_asset_weight = Decimal(1)
                perp_init_liab_weight = Decimal(1)
                perp_maint_liab_weight = Decimal(1)

            base_open_unsettled: Decimal = Decimal(0)
            base_open_locked: Decimal = Decimal(0)
            base_open_total: Decimal = Decimal(0)
            base_open_total_value: Decimal = Decimal(0)
            quote_open_unsettled: Decimal = Decimal(0)
            quote_open_locked: Decimal = Decimal(0)
            if spot_open_orders is not None:
                if (
                    slot.index < len(self.in_margin_basket)
                    and self.in_margin_basket[slot.index]
                ):
                    base_open_unsettled = spot_open_orders.base_token_free
                    base_open_locked = spot_open_orders.base_token_locked
                    base_open_total = spot_open_orders.base_token_total
                    base_open_total_value = base_open_total * price.value

                # Some calculations include quote unsettled whether it's in
                # the margin basket or not.
                quote_open_unsettled = (
                    spot_open_orders.quote_token_free
                    + spot_open_orders.referrer_rebate_accrued
                )
                quote_open_locked = spot_open_orders.quote_token_locked
            base_total: Decimal = (
                slot.deposit.value - slot.borrow.value + base_open_total
            )

            base_total_value: Decimal = base_total * price.value
            data = {
                "Name": slot.base_instrument.name,
                "Symbol": slot.base_instrument.symbol,
                "InMarginBasket": slot.index < len(self.in_margin_basket)
                and self.in_margin_basket[slot.index],
                "CurrentPrice": price.value,
                "Spot": base_total,
                "SpotValue": base_total_value,
                "SpotDeposit": slot.deposit.value,
                "SpotDepositValue": slot.deposit.value * price.value,
                "SpotBorrow": slot.borrow.value,
                "SpotBorrowValue": slot.borrow.value * price.value * Decimal(-1),
                "SpotOpen": base_open_total,
                "SpotOpenValue": base_open_total_value,
                "BaseUnsettled": base_open_unsettled,
                "BaseLocked": base_open_locked,
                "BaseLockedValue": base_open_locked * price.value,
                "QuoteUnsettled": quote_open_unsettled,
                "QuoteLocked": quote_open_locked,
                "PerpPositionSize": perp_position,
                "PerpNotionalSize": perp_notional_position,
                "SpotHealthBase": spot_health_base,
                "SpotHealthBaseValue": spot_health_base * price.value,
                "SpotHealthQuote": spot_health_quote,
                "PerpHealthBase": perp_health_base,
                "PerpHealthBaseValue": perp_health_base_value,
                "PerpHealthQuote": perp_health_quote,
                "PerpAsset": perp_asset,
                "PerpLiability": perp_liability,
                "RedeemablePnL": redeemable_pnl,
                "UnsettledFunding": unsettled_funding,
                "SpotInitAssetWeight": spot_init_asset_weight,
                "SpotMaintAssetWeight": spot_maint_asset_weight,
                "SpotInitLiabilityWeight": spot_init_liab_weight,
                "SpotMaintLiabilityWeight": spot_maint_liab_weight,
                "PerpInitAssetWeight": perp_init_asset_weight,
                "PerpMaintAssetWeight": perp_maint_asset_weight,
                "PerpInitLiabilityWeight": perp_init_liab_weight,
                "PerpMaintLiabilityWeight": perp_maint_liab_weight,
                "BaseDecimals": slot.base_instrument.decimals,
                "QuoteDecimals": group.shared_quote_token.decimals,
                "PerpBaseLotSize": perp_base_lot_size,
                "PerpQuoteLotSize": perp_quote_lot_size,
            }
            asset_data += [data]
        frame: pandas.DataFrame = pandas.DataFrame(asset_data)
        return frame

    def weighted_assets(
        self, frame: pandas.DataFrame, weighting_name: str = ""
    ) -> typing.Tuple[Decimal, Decimal]:
        non_quote = frame.loc[frame["Symbol"] != self.shared_quote_token.symbol]
        quote = frame.loc[
            frame["Symbol"] == self.shared_quote_token.symbol, "SpotValue"
        ].sum()
        quote += frame["PerpHealthQuote"].sum()

        # Sometimes there is QuoteUnsettled when the instrument is no longer in the margin
        # basket. Those values are excluded here to match the behaviour of the TypeScript
        # client so our answers match.
        quote += frame.loc[frame["InMarginBasket"], "QuoteUnsettled"].sum()

        assets = Decimal(0)
        liabilities = Decimal(0)
        if quote > 0:
            assets = quote
        else:
            liabilities = quote

        spot_borrow_health = (
            non_quote.loc[non_quote["SpotHealthBaseValue"] < 0, "SpotHealthBaseValue"]
            * non_quote[f"Spot{weighting_name}LiabilityWeight"]
        ).sum()

        perp_health_base_liability = (
            non_quote.loc[non_quote["PerpHealthBaseValue"] < 0, "PerpHealthBaseValue"]
            * non_quote[f"Perp{weighting_name}LiabilityWeight"]
        ).sum()

        liabilities += spot_borrow_health + perp_health_base_liability

        spot_deposit_health = (
            (non_quote.loc[non_quote["SpotHealthBaseValue"] > 0, "SpotHealthBaseValue"])
            * non_quote[f"Spot{weighting_name}AssetWeight"]
        ).sum()

        perp_health_base_asset = (
            non_quote.loc[non_quote["PerpHealthBaseValue"] > 0, "PerpHealthBaseValue"]
            * non_quote[f"Perp{weighting_name}AssetWeight"]
        ).sum()

        assets += spot_deposit_health + perp_health_base_asset

        return assets, liabilities

    def unweighted_assets(
        self, frame: pandas.DataFrame
    ) -> typing.Tuple[Decimal, Decimal]:
        non_quote = frame.loc[frame["Symbol"] != self.shared_quote_token.symbol]
        quote = frame.loc[
            frame["Symbol"] == self.shared_quote_token.symbol, "SpotValue"
        ].sum()

        assets = Decimal(0)
        liabilities = Decimal(0)
        if quote > 0:
            assets = quote
        else:
            liabilities = quote

        liabilities += (
            non_quote["SpotBorrowValue"].sum() + non_quote["PerpLiability"].sum()
        )

        assets += (
            non_quote["SpotDepositValue"].sum()
            + non_quote["BaseLockedValue"].sum()
            + non_quote["PerpAsset"].sum()
            + non_quote["QuoteUnsettled"].sum()
            + non_quote["QuoteLocked"].sum()
        )

        return assets, liabilities

    def init_health(self, frame: pandas.DataFrame) -> InstrumentValue:
        assets, liabilities = self.weighted_assets(frame, "Init")
        value: Decimal = assets + liabilities
        return InstrumentValue(self.shared_quote_token, value)

    def maint_health(self, frame: pandas.DataFrame) -> InstrumentValue:
        assets, liabilities = self.weighted_assets(frame, "Maint")
        value: Decimal = assets + liabilities
        return InstrumentValue(self.shared_quote_token, value)

    def init_health_ratio(self, frame: pandas.DataFrame) -> Decimal:
        assets, liabilities = self.weighted_assets(frame, "Init")
        if liabilities == 0:
            return Decimal(100)

        return ((assets / -liabilities) - 1) * 100

    def maint_health_ratio(self, frame: pandas.DataFrame) -> Decimal:
        assets, liabilities = self.weighted_assets(frame, "Maint")
        if liabilities == 0:
            return Decimal(100)

        return ((assets / -liabilities) - 1) * 100

    def total_value(self, frame: pandas.DataFrame) -> InstrumentValue:
        assets, liabilities = self.unweighted_assets(frame)

        value: Decimal = assets + liabilities
        return InstrumentValue(self.shared_quote_token, value)

    def is_liquidatable(self, frame: pandas.DataFrame) -> bool:
        if self.being_liquidated and self.init_health(frame) < 0:
            return True
        elif self.maint_health(frame) < 0:
            return True
        return False

    def leverage(self, frame: pandas.DataFrame) -> Decimal:
        assets, liabilities = self.unweighted_assets(frame)
        if assets <= 0:
            return Decimal(0)
        return -liabilities / (assets + liabilities)

    def redeemable_pnl(self, frame: pandas.DataFrame) -> InstrumentValue:
        value: Decimal = frame["RedeemablePnL"].sum()
        return InstrumentValue(self.shared_quote_token, value)

    def __str__(self) -> str:
        info = f"'{self.info}'" if self.info else "(un-named)"
        shared_quote: str = f"{self.shared_quote}".replace("\n", "\n        ")
        slot_count = len(self.base_slots)
        slots = "\n        ".join(
            [f"{item}".replace("\n", "\n        ") for item in self.base_slots]
        )

        symbols: typing.Sequence[str] = [
            slot.base_instrument.symbol for slot in self.base_slots
        ]
        in_margin_basket = ", ".join(symbols) or "None"
        return f"""« Account {info}, {self.version} [{self.address}]
    {self.meta_data}
    Owner: {self.owner}
    Delegated To: {self.delegate}
    Group: « Group '{self.group_name}' [{self.group_address}] »
    Advanced Orders Account: {self.advanced_orders}
    MSRM: {self.msrm_amount}
    Bankrupt? {self.is_bankrupt}
    Upgradable? {not self.not_upgradable}
    Being Liquidated? {self.being_liquidated}
    Shared Quote Token:
        {shared_quote}
    In Basket: {in_margin_basket}
    Basket [{slot_count} in basket]:
        {slots}
»"""

    def __repr__(self) -> str:
        return f"{self}"


@dataclass
class Valuation:
    account: Account
    open_orders: typing.Dict[str, OpenOrders]
    frame: pandas.DataFrame
    total_value: InstrumentValue

    @property
    def init_health(self) -> InstrumentValue:
        return self.account.init_health(self.frame)

    @property
    def maint_health(self) -> InstrumentValue:
        return self.account.maint_health(self.frame)

    @property
    def init_health_ratio(self) -> Decimal:
        return self.account.init_health_ratio(self.frame)

    @property
    def maint_health_ratio(self) -> Decimal:
        return self.account.maint_health_ratio(self.frame)

    @property
    def is_liquidatable(self) -> bool:
        return self.account.is_liquidatable(self.frame)

    @property
    def leverage(self) -> Decimal:
        return self.account.leverage(self.frame)

    @property
    def redeemable_pnl(self) -> InstrumentValue:
        return self.account.redeemable_pnl(self.frame)

    @staticmethod
    def create(
        account: Account,
        group: Group,
        open_orders_data: typing.Dict[str, AccountInfo],
        cache: Cache,
    ) -> "Valuation":
        oos = {}
        for slot in account.slots:
            if slot.spot_open_orders is not None:
                oo = OpenOrders.parse(
                    open_orders_data[str(slot.spot_open_orders)],
                    Token.ensure(slot.base_instrument),
                    group.shared_quote_token,
                )
                oos[str(oo.address)] = oo
        frame = account.to_dataframe(group, oos, cache)
        value = account.total_value(frame)
        return Valuation(account, oos, frame, value)

    def __lt__(self, other: "Valuation") -> bool:
        return self.total_value.value < other.total_value.value

    def __le__(self, other: "Valuation") -> bool:
        return self.total_value.value <= other.total_value.value

    def __gt__(self, other: "Valuation") -> bool:
        return self.total_value.value > other.total_value.value

    def __ge__(self, other: "Valuation") -> bool:
        return self.total_value.value >= other.total_value.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Valuation):
            return self.total_value.value == other.total_value.value
        return False

    def __ne__(self, other: object) -> bool:
        if isinstance(other, Valuation):
            return self.total_value.value != other.total_value.value
        return True

    def __str__(self) -> str:
        return f"""« Valuation {str(self.account.address):<44} {self.total_value.value:>25,.8f} {self.total_value.token.symbol} »"""

    def __repr__(self) -> str:
        return f"{self}"
