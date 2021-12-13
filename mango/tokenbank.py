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

from datetime import datetime
from decimal import Decimal
from solana.publickey import PublicKey

from .accountinfo import AccountInfo
from .addressableaccount import AddressableAccount
from .cache import RootBankCache, Cache
from .context import Context
from .instrumentlookup import InstrumentLookup
from .layouts import layouts
from .metadata import Metadata
from .token import Instrument, Token
from .version import Version


# # 🥭 InterestRates class
#
# A simple way to package borrow and deposit rates together in a single object.
#
class InterestRates(typing.NamedTuple):
    deposit: Decimal
    borrow: Decimal

    def __str__(self) -> str:
        return f"« InterestRates Deposit: {self.deposit:,.2%} Borrow: {self.borrow:,.2%} »"

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 BankBalances class
#
# A simple way to package borrow and deposit balances together in a single object.
#
class BankBalances(typing.NamedTuple):
    deposits: Decimal
    borrows: Decimal

    def __str__(self) -> str:
        return f"« BankBalances Deposits: {self.deposits:,.8f} Borrows: {self.borrows:,.8f} »"

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 NodeBank class
#
# `NodeBank` stores details of deposits/borrows and vault.
#
class NodeBank(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version, meta_data: Metadata,
                 vault: PublicKey, balances: BankBalances) -> None:
        super().__init__(account_info)
        self.version: Version = version
        self.meta_data: Metadata = meta_data
        self.vault: PublicKey = vault
        self.balances: BankBalances = balances

    @staticmethod
    def from_layout(layout: typing.Any, account_info: AccountInfo, version: Version) -> "NodeBank":
        meta_data: Metadata = layout.meta_data
        deposits: Decimal = layout.deposits
        borrows: Decimal = layout.borrows
        balances: BankBalances = BankBalances(deposits=deposits, borrows=borrows)
        vault: PublicKey = layout.vault

        return NodeBank(account_info, version, meta_data, vault, balances)

    @staticmethod
    def parse(account_info: AccountInfo) -> "NodeBank":
        data = account_info.data
        if len(data) != layouts.NODE_BANK.sizeof():
            raise Exception(
                f"NodeBank data length ({len(data)}) does not match expected size ({layouts.NODE_BANK.sizeof()})")

        layout = layouts.NODE_BANK.parse(data)
        return NodeBank.from_layout(layout, account_info, Version.V1)

    @staticmethod
    def load(context: Context, address: PublicKey) -> "NodeBank":
        account_info = AccountInfo.load(context, address)
        if account_info is None:
            raise Exception(f"NodeBank account not found at address '{address}'")
        return NodeBank.parse(account_info)

    def __str__(self) -> str:
        return f"""« NodeBank [{self.version}] {self.address}
    {self.meta_data}
    Balances: {self.balances}
    Vault: {self.vault}
»"""

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 RootBank class
#
# `RootBank` stores details of how to reach `NodeBank`.
#
class RootBank(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version, meta_data: Metadata,
                 optimal_util: Decimal, optimal_rate: Decimal, max_rate: Decimal,
                 node_banks: typing.Sequence[PublicKey], deposit_index: Decimal,
                 borrow_index: Decimal, last_updated: datetime) -> None:
        super().__init__(account_info)
        self.version: Version = version

        self.meta_data: Metadata = meta_data

        self.optimal_util: Decimal = optimal_util
        self.optimal_rate: Decimal = optimal_rate
        self.max_rate: Decimal = max_rate

        self.node_banks: typing.Sequence[PublicKey] = node_banks
        self.deposit_index: Decimal = deposit_index
        self.borrow_index: Decimal = borrow_index
        self.last_updated: datetime = last_updated

        self.loaded_node_banks: typing.Optional[typing.Sequence[NodeBank]] = None

    def ensure_node_banks(self, context: Context) -> typing.Sequence[NodeBank]:
        if self.loaded_node_banks is None:
            node_bank_account_infos = AccountInfo.load_multiple(context, self.node_banks)
            self.loaded_node_banks = list(map(NodeBank.parse, node_bank_account_infos))
        return self.loaded_node_banks

    def pick_node_bank(self, context: Context) -> NodeBank:
        return self.ensure_node_banks(context)[0]

    def fetch_balances(self, context: Context) -> BankBalances:
        node_banks: typing.Sequence[NodeBank] = self.ensure_node_banks(context)

        deposits_in_node_banks: Decimal = Decimal(0)
        borrows_in_node_banks: Decimal = Decimal(0)
        for node_bank in node_banks:
            deposits_in_node_banks += node_bank.balances.deposits
            borrows_in_node_banks += node_bank.balances.borrows

        total_deposits: Decimal = deposits_in_node_banks * self.deposit_index
        total_borrows: Decimal = borrows_in_node_banks * self.borrow_index

        return BankBalances(deposits=total_deposits, borrows=total_borrows)

    @staticmethod
    def from_layout(layout: typing.Any, account_info: AccountInfo, version: Version) -> "RootBank":
        meta_data: Metadata = Metadata.from_layout(layout.meta_data)

        optimal_util: Decimal = layout.optimal_util
        optimal_rate: Decimal = layout.optimal_rate
        max_rate: Decimal = layout.max_rate

        num_node_banks: Decimal = layout.num_node_banks
        node_banks: typing.Sequence[PublicKey] = layout.node_banks[0:int(num_node_banks)]
        deposit_index: Decimal = layout.deposit_index
        borrow_index: Decimal = layout.borrow_index
        last_updated: datetime = layout.last_updated

        return RootBank(account_info, version, meta_data, optimal_util, optimal_rate, max_rate, node_banks, deposit_index, borrow_index, last_updated)

    @staticmethod
    def parse(account_info: AccountInfo) -> "RootBank":
        data = account_info.data
        if len(data) != layouts.ROOT_BANK.sizeof():
            raise Exception(
                f"RootBank data length ({len(data)}) does not match expected size ({layouts.ROOT_BANK.sizeof()})")

        layout = layouts.ROOT_BANK.parse(data)
        return RootBank.from_layout(layout, account_info, Version.V1)

    @staticmethod
    def load(context: Context, address: PublicKey) -> "RootBank":
        account_info = AccountInfo.load(context, address)
        if account_info is None:
            raise Exception(f"RootBank account not found at address '{address}'")
        return RootBank.parse(account_info)

    @staticmethod
    def load_multiple(context: Context, addresses: typing.Sequence[PublicKey]) -> typing.Sequence["RootBank"]:
        account_infos = AccountInfo.load_multiple(context, addresses)
        root_banks = []
        for account_info in account_infos:
            root_bank = RootBank.parse(account_info)
            root_banks += [root_bank]

        return root_banks

    @staticmethod
    def find_by_address(values: typing.Sequence["RootBank"], address: PublicKey) -> "RootBank":
        found = [value for value in values if value.address == address]
        if len(found) == 0:
            raise Exception(f"RootBank '{address}' not found in root banks: {values}")

        if len(found) > 1:
            raise Exception(f"RootBank '{address}' matched multiple root banks in: {values}")

        return found[0]

    def __str__(self) -> str:
        return f"""« RootBank [{self.version}] {self.address}
    {self.meta_data}
    Optimal Util: {self.optimal_util:,.4f}
    Optimal Rate: {self.optimal_rate:,.4f}
    Max Rate: {self.max_rate}
    Node Banks:
        {self.node_banks}
    Deposit Index: {self.deposit_index}
    Borrow Index: {self.borrow_index}
    Last Updated: {self.last_updated}
»"""

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 TokenBank class
#
# `TokenBank` defines additional information for a `Token`.
#
class TokenBank():
    def __init__(self, token: Token, root_bank_address: PublicKey) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.token: Token = token
        self.root_bank_address: PublicKey = root_bank_address

        self.loaded_root_bank: typing.Optional[RootBank] = None

    @staticmethod
    def from_layout_or_none(layout: typing.Any, instrument_lookup: InstrumentLookup) -> typing.Optional["TokenBank"]:
        if layout.mint is None:
            return None

        instrument: typing.Optional[Instrument] = instrument_lookup.find_by_mint(layout.mint)
        if instrument is None:
            raise Exception(f"Token with mint {layout.mint} could not be found.")
        token: Token = Token.ensure(instrument)
        root_bank_address: PublicKey = layout.root_bank
        decimals: Decimal = layout.decimals

        if decimals != token.decimals:
            raise Exception(
                f"Conflict between number of decimals in token static data {token.decimals} and group {decimals} for token {token.symbol}.")

        return TokenBank(token, root_bank_address)

    @staticmethod
    def find_by_symbol(values: typing.Sequence[typing.Optional["TokenBank"]], symbol: str) -> "TokenBank":
        found = [
            value for value in values if value is not None and value.token is not None and value.token.symbol_matches(symbol)]
        if len(found) == 0:
            raise Exception(f"Token '{symbol}' not found in token infos: {values}")

        if len(found) > 1:
            raise Exception(f"Token '{symbol}' matched multiple tokens in infos: {values}")

        return found[0]

    def root_bank_cache_from_cache(self, cache: Cache, index: int) -> typing.Optional[RootBankCache]:
        return cache.root_bank_cache[index]

    def ensure_root_bank(self, context: Context) -> RootBank:
        if self.loaded_root_bank is None:
            self.loaded_root_bank = RootBank.load(context, self.root_bank_address)
        return self.loaded_root_bank

    def pick_node_bank(self, context: Context) -> NodeBank:
        root_bank: RootBank = self.ensure_root_bank(context)
        return root_bank.pick_node_bank(context)

    def fetch_interest_rates(self, context: Context) -> InterestRates:
        root_bank: RootBank = self.ensure_root_bank(context)
        balances: BankBalances = root_bank.fetch_balances(context)

        borrow_rate: Decimal = Decimal(0)
        deposit_rate: Decimal = Decimal(0)
        utilization: Decimal
        if balances.deposits != 0 and balances.borrows != 0:
            if balances.deposits <= balances.borrows:
                borrow_rate = root_bank.max_rate
            else:
                utilization = balances.borrows / balances.deposits
                slope: Decimal
                if utilization < root_bank.optimal_util:
                    slope = root_bank.optimal_rate / root_bank.optimal_util
                    borrow_rate = slope * utilization
                else:
                    extra_utilization = utilization - root_bank.optimal_util
                    slope = (root_bank.max_rate - root_bank.optimal_rate) / (1 - root_bank.optimal_util)
                    borrow_rate = root_bank.optimal_rate + (slope * extra_utilization)

            if balances.deposits == 0:
                deposit_rate = root_bank.max_rate
            else:
                utilization = balances.borrows / balances.deposits
                deposit_rate = utilization * borrow_rate

        return InterestRates(deposit=deposit_rate, borrow=borrow_rate)

    def __str__(self) -> str:
        return f"""« TokenBank {self.token}
    Root Bank Address: {self.root_bank_address}
»"""

    def __repr__(self) -> str:
        return f"{self}"
