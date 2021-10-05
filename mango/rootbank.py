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

from datetime import datetime
from decimal import Decimal
from solana.publickey import PublicKey

from .accountinfo import AccountInfo
from .addressableaccount import AddressableAccount
from .context import Context
from .layouts import layouts
from .metadata import Metadata
from .version import Version


# # 🥭 NodeBank class
#
# `NodeBank` stores details of deposits/borrows and vault.
#
class NodeBank(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version, meta_data: Metadata,
                 deposits: Decimal, borrows: Decimal, vault: PublicKey):
        super().__init__(account_info)
        self.version: Version = version

        self.meta_data: Metadata = meta_data
        self.deposits: Decimal = deposits
        self.borrows: Decimal = borrows
        self.vault: PublicKey = vault

    @staticmethod
    def from_layout(layout: typing.Any, account_info: AccountInfo, version: Version) -> "NodeBank":
        meta_data: Metadata = layout.meta_data
        deposits: Decimal = layout.deposits
        borrows: Decimal = layout.borrows
        vault: PublicKey = layout.vault

        return NodeBank(account_info, version, meta_data, deposits, borrows, vault)

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
        return f"""« 𝙽𝚘𝚍𝚎𝙱𝚊𝚗𝚔 [{self.version}] {self.address}
    {self.meta_data}
    Deposit: {self.deposits}
    Borrow: {self.borrows}
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
                 borrow_index: Decimal, last_updated: datetime):
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

    def pick_node_bank(self, context: Context) -> NodeBank:
        node_bank_account_infos = AccountInfo.load_multiple(context, self.node_banks)
        return list(map(NodeBank.parse, node_bank_account_infos))[0]

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
        return f"""« 𝚁𝚘𝚘𝚝𝙱𝚊𝚗𝚔 [{self.version}] {self.address}
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
