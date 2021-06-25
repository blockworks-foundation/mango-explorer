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


import abc
import logging
import typing

from decimal import Decimal
from pyserum.enums import OrderType, Side
from pyserum.instructions import ConsumeEventsParams, consume_events, settle_funds, SettleFundsParams
from pyserum.market import Market
from pyserum.open_orders_account import make_create_account_instruction
from solana.account import Account
from solana.publickey import PublicKey
from solana.system_program import CreateAccountParams, create_account
from solana.transaction import AccountMeta, TransactionInstruction
from spl.token.constants import ACCOUNT_LEN, TOKEN_PROGRAM_ID
from spl.token.instructions import CloseAccountParams, InitializeAccountParams, Transfer2Params, close_account, initialize_account, transfer2

from .context import Context
from .layouts import layouts
from .token import Token
from .wallet import Wallet


# 🥭 Instructions
#
# This notebook contains the low-level `InstructionBuilder`s that build the raw instructions
# to send to Solana.
#

# # 🥭 InstructionBuilder class
#
# An abstract base class for all our `InstructionBuilder`s.
#

class InstructionBuilder(metaclass=abc.ABCMeta):
    def __init__(self, context: Context):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.context = context

    @abc.abstractmethod
    def build(self) -> TransactionInstruction:
        raise NotImplementedError("InstructionBuilder.build() is not implemented on the base class.")

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 CreateSplAccountInstructionBuilder class
#
# Creates an SPL token account. Can't do much with it without following by an
# `InitializeSplAccountInstructionBuilder`.
#

class CreateSplAccountInstructionBuilder(InstructionBuilder):
    def __init__(self, context: Context, wallet: Wallet, address: PublicKey, lamports: int = 0):
        super().__init__(context)
        self.wallet: Wallet = wallet
        self.address: PublicKey = address
        self.lamports: int = lamports

    def build(self) -> TransactionInstruction:
        minimum_balance_response = self.context.client.get_minimum_balance_for_rent_exemption(
            ACCOUNT_LEN, commitment=self.context.commitment)
        minimum_balance = self.context.unwrap_or_raise_exception(minimum_balance_response)
        return create_account(
            CreateAccountParams(self.wallet.address, self.address, self.lamports + minimum_balance, ACCOUNT_LEN, TOKEN_PROGRAM_ID))


# # 🥭 InitializeSplAccountInstructionBuilder class
#
# Initialises an SPL token account, presumably created by a previous
# `CreateSplAccountInstructionBuilder` instruction.
#

class InitializeSplAccountInstructionBuilder(InstructionBuilder):
    def __init__(self, context: Context, wallet: Wallet, token: Token, address: PublicKey):
        super().__init__(context)
        self.wallet: Wallet = wallet
        self.token: Token = token
        self.address: PublicKey = address

    def build(self) -> TransactionInstruction:
        return initialize_account(
            InitializeAccountParams(TOKEN_PROGRAM_ID, self.address, self.token.mint, self.wallet.address))


# # 🥭 TransferSplTokensInstructionBuilder class
#
# Creates a `TransactionInstruction` that can transfer SPL tokens from one account to
# another.
#

class TransferSplTokensInstructionBuilder(InstructionBuilder):
    def __init__(self, context: Context, wallet: Wallet, token: Token, source: PublicKey, destination: PublicKey, quantity: Decimal):
        super().__init__(context)
        self.wallet: Wallet = wallet
        self.token: Token = token
        self.source: PublicKey = source
        self.destination: PublicKey = destination
        self.amount = int(quantity * (10 ** token.decimals))

    def build(self) -> TransactionInstruction:
        return transfer2(
            Transfer2Params(TOKEN_PROGRAM_ID, self.source, self.token.mint, self.destination, self.wallet.address, self.amount, int(self.token.decimals)))


# # 🥭 CloseSplAccountInstructionBuilder class
#
# Closes an SPL token account and transfers any remaining lamports to the wallet.
#

class CloseSplAccountInstructionBuilder(InstructionBuilder):
    def __init__(self, context: Context, wallet: Wallet, address: PublicKey):
        super().__init__(context)
        self.wallet: Wallet = wallet
        self.address: PublicKey = address

    def build(self) -> TransactionInstruction:
        return close_account(
            CloseAccountParams(TOKEN_PROGRAM_ID, self.address, self.wallet.address, self.wallet.address))


# # 🥭 CreateSerumOpenOrdersInstructionBuilder class
#
# Creates a Serum openorders-creating instruction.
#
class CreateSerumOpenOrdersInstructionBuilder(InstructionBuilder):
    def __init__(self, context: Context, wallet: Wallet, market: Market, open_orders_address: PublicKey):
        super().__init__(context)
        self.wallet: Wallet = wallet
        self.market: Market = market
        self.open_orders_address: PublicKey = open_orders_address

    def build(self) -> TransactionInstruction:
        response = self.context.client.get_minimum_balance_for_rent_exemption(
            layouts.OPEN_ORDERS.sizeof(), commitment=self.context.commitment)
        balanced_needed = self.context.unwrap_or_raise_exception(response)
        instruction = make_create_account_instruction(
            owner_address=self.wallet.address,
            new_account_address=self.open_orders_address,
            lamports=balanced_needed,
            program_id=self.market.state.program_id(),
        )

        return instruction

    def __str__(self) -> str:
        return f"""« CreateSerumOpenOrdersInstructionBuilder:
    owner_address: {self.wallet.address},
    new_account_address: {self.open_orders_address},
    program_id: {self.market.state.program_id()}
»"""


# # 🥭 NewOrderV3InstructionBuilder class
#
# Creates a Serum order-placing instruction using V3 of the NewOrder instruction.
#
class NewOrderV3InstructionBuilder(InstructionBuilder):
    def __init__(self, context: Context, wallet: Wallet, market: Market, source: PublicKey, open_orders_address: PublicKey, order_type: OrderType, side: Side, price: Decimal, quantity: Decimal, client_id: int, fee_discount_address: typing.Optional[PublicKey]):
        super().__init__(context)
        self.wallet: Wallet = wallet
        self.market: Market = market
        self.source: PublicKey = source
        self.open_orders_address: PublicKey = open_orders_address
        self.order_type: OrderType = order_type
        self.side: Side = side
        self.price: Decimal = price
        self.quantity: Decimal = quantity
        self.client_id: int = client_id
        self.fee_discount_address: typing.Optional[PublicKey] = fee_discount_address

    def build(self) -> TransactionInstruction:
        instruction = self.market.make_place_order_instruction(
            self.source,
            self.wallet.account,
            self.order_type,
            self.side,
            float(self.price),
            float(self.quantity),
            self.client_id,
            self.open_orders_address,
            self.fee_discount_address
        )

        return instruction

    def __str__(self) -> str:
        return f"""« NewOrderV3InstructionBuilder:
    source.address: {self.source},
    wallet.account: {self.wallet.account.public_key()},
    order_type: {self.order_type},
    side: {self.side},
    price: {float(self.price)},
    quantity: {float(self.quantity)},
    client_id: {self.client_id},
    open_orders_address: {self.open_orders_address}
    fee_discount_address: {self.fee_discount_address}
»"""


# # 🥭 ConsumeEventsInstructionBuilder class
#
# Creates an event-consuming 'crank' instruction.
#
class ConsumeEventsInstructionBuilder(InstructionBuilder):
    def __init__(self, context: Context, wallet: Wallet, market: Market, open_orders_addresses: typing.Sequence[PublicKey], limit: int = 32):
        super().__init__(context)
        self.wallet: Wallet = wallet
        self.market: Market = market
        self.open_orders_addresses: typing.Sequence[PublicKey] = open_orders_addresses
        self.limit: int = limit

    def build(self) -> TransactionInstruction:
        instruction = consume_events(ConsumeEventsParams(
            market=self.market.state.public_key(),
            event_queue=self.market.state.event_queue(),
            open_orders_accounts=self.open_orders_addresses,
            limit=32
        ))

        # The interface accepts (and currently requires) two accounts at the end, but
        # it doesn't actually use them.
        random_account = Account().public_key()
        instruction.keys.append(AccountMeta(random_account, is_signer=False, is_writable=False))
        instruction.keys.append(AccountMeta(random_account, is_signer=False, is_writable=False))
        return instruction

    def __str__(self) -> str:
        return f"""« ConsumeEventsInstructionBuilder:
    market: {self.market.state.public_key()},
    event_queue: {self.market.state.event_queue()},
    open_orders_accounts: {self.open_orders_addresses},
    limit: {self.limit}
»"""


# # 🥭 SettleInstructionBuilder class
#
# Creates a 'settle' instruction.
#
class SettleInstructionBuilder(InstructionBuilder):
    def __init__(self, context: Context, wallet: Wallet, market: Market, open_orders_address: PublicKey, base_token_account_address: PublicKey, quote_token_account_address: PublicKey):
        super().__init__(context)
        self.wallet: Wallet = wallet
        self.market: Market = market
        self.base_token_account_address: PublicKey = base_token_account_address
        self.quote_token_account_address: PublicKey = quote_token_account_address
        self.open_orders_address: PublicKey = open_orders_address
        self.vault_signer = PublicKey.create_program_address(
            [bytes(self.market.state.public_key()), self.market.state.vault_signer_nonce().to_bytes(8, byteorder="little")],
            self.market.state.program_id(),
        )

    def build(self) -> TransactionInstruction:
        instruction = settle_funds(
            SettleFundsParams(
                market=self.market.state.public_key(),
                open_orders=self.open_orders_address,
                owner=self.wallet.address,
                base_vault=self.market.state.base_vault(),
                quote_vault=self.market.state.quote_vault(),
                base_wallet=self.base_token_account_address,
                quote_wallet=self.quote_token_account_address,
                vault_signer=self.vault_signer,
                program_id=self.market.state.program_id(),
            )
        )

        return instruction

    def __str__(self) -> str:
        return f"""« SettleInstructionBuilder:
    market: {self.market.state.public_key()},
    base_token_account: {self.base_token_account_address},
    quote_token_account: {self.quote_token_account_address},
    vault_signer: {self.vault_signer}
»"""
