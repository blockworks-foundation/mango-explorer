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
from pyserum.enums import OrderType as SerumOrderType, Side as SerumSide
from pyserum.instructions import ConsumeEventsParams, consume_events, settle_funds, SettleFundsParams
from pyserum.market import Market
from pyserum.open_orders_account import make_create_account_instruction
from solana.account import Account as SolanaAccount
from solana.publickey import PublicKey
from solana.system_program import CreateAccountParams, create_account
from solana.sysvar import SYSVAR_CLOCK_PUBKEY
from solana.transaction import AccountMeta, TransactionInstruction
from spl.token.constants import ACCOUNT_LEN, TOKEN_PROGRAM_ID
from spl.token.instructions import CloseAccountParams, InitializeAccountParams, Transfer2Params, close_account, initialize_account, transfer2

from .account import Account
from .constants import SYSTEM_PROGRAM_ADDRESS
from .context import Context
from .group import Group
from .layouts import layouts
from .orders import Order, OrderType, Side
from .perpmarket import PerpMarket
from .rootbank import NodeBank, RootBank
from .token import Token
from .tokenaccount import TokenAccount
from .wallet import Wallet


# 🥭 Instructions
#
# This file contains the low-level instruction functions that build the raw instructions
# to send to Solana.
#
# One important distinction between these functions and the more common `create instruction functions` in
# Solana is that these functions *all return a list of instructions*.
#
# It's likely that some operations will require actions split across multiple instructions because of
# instruction size limitiations, so all our functions are prepared for this without having to change
# the function signature in future.
#


# # 🥭 build_create_spl_account_instructions function
#
# Creates and initializes an SPL token account. Can add additional lamports too but that's usually not
# necesary.
#

def build_create_spl_account_instructions(context: Context, wallet: Wallet, token: Token, address: PublicKey, lamports: int = 0) -> typing.Sequence[TransactionInstruction]:
    minimum_balance_response = context.client.get_minimum_balance_for_rent_exemption(
        ACCOUNT_LEN, commitment=context.commitment)
    minimum_balance = context.unwrap_or_raise_exception(minimum_balance_response)
    create_instruction = create_account(
        CreateAccountParams(wallet.address, address, lamports + minimum_balance, ACCOUNT_LEN, TOKEN_PROGRAM_ID))
    initialize_instruction = initialize_account(
        InitializeAccountParams(TOKEN_PROGRAM_ID, address, token.mint, wallet.address))
    return [create_instruction, initialize_instruction]


# # 🥭 build_transfer_spl_tokens_instructions function
#
# Creates an instruction to transfer SPL tokens from one account to another.
#

def build_transfer_spl_tokens_instructions(context: Context, wallet: Wallet, token: Token, source: PublicKey, destination: PublicKey, quantity: Decimal) -> typing.Sequence[TransactionInstruction]:
    amount = int(quantity * (10 ** token.decimals))
    return [transfer2(Transfer2Params(TOKEN_PROGRAM_ID, source, token.mint, destination, wallet.address, amount, int(token.decimals)))]


# # 🥭 build_close_spl_account_instructions function
#
# Creates an instructio to close an SPL token account and transfers any remaining lamports to the wallet.
#

def build_close_spl_account_instructions(context: Context, wallet: Wallet, address: PublicKey) -> typing.Sequence[TransactionInstruction]:
    return [close_account(CloseAccountParams(TOKEN_PROGRAM_ID, address, wallet.address, wallet.address))]


# # 🥭 build_create_serum_open_orders_instructions function
#
# Creates a Serum openorders-creating instruction.
#

def build_create_serum_open_orders_instructions(context: Context, wallet: Wallet, market: Market, open_orders_address: PublicKey) -> typing.Sequence[TransactionInstruction]:
    response = context.client.get_minimum_balance_for_rent_exemption(
        layouts.OPEN_ORDERS.sizeof(), commitment=context.commitment)
    balanced_needed = context.unwrap_or_raise_exception(response)
    instruction = make_create_account_instruction(
        owner_address=wallet.address,
        new_account_address=open_orders_address,
        lamports=balanced_needed,
        program_id=market.state.program_id(),
    )

    return [instruction]


# # 🥭 build_serum_place_order_instructions function
#
# Creates a Serum order-placing instruction using V3 of the NewOrder instruction.
#

def build_serum_place_order_instructions(context: Context, wallet: Wallet, market: Market, source: PublicKey, open_orders_address: PublicKey, order_type: OrderType, side: Side, price: Decimal, quantity: Decimal, client_id: int, fee_discount_address: typing.Optional[PublicKey]) -> typing.Sequence[TransactionInstruction]:
    serum_order_type: SerumOrderType = SerumOrderType.POST_ONLY if order_type == OrderType.POST_ONLY else SerumOrderType.IOC if order_type == OrderType.IOC else SerumOrderType.LIMIT
    serum_side: SerumSide = SerumSide.SELL if side == Side.SELL else SerumSide.BUY

    instruction = market.make_place_order_instruction(
        source,
        wallet.account,
        serum_order_type,
        serum_side,
        float(price),
        float(quantity),
        client_id,
        open_orders_address,
        fee_discount_address
    )

    return [instruction]


# # 🥭 build_serum_consume_events_instructions function
#
# Creates an event-consuming 'crank' instruction.
#

def build_serum_consume_events_instructions(context: Context, wallet: Wallet, market: Market, open_orders_addresses: typing.Sequence[PublicKey], limit: int = 32) -> typing.Sequence[TransactionInstruction]:
    instruction = consume_events(ConsumeEventsParams(
        market=market.state.public_key(),
        event_queue=market.state.event_queue(),
        open_orders_accounts=open_orders_addresses,
        limit=limit
    ))

    # The interface accepts (and currently requires) two accounts at the end, but
    # it doesn't actually use them.
    random_account = SolanaAccount().public_key()
    instruction.keys.append(AccountMeta(random_account, is_signer=False, is_writable=False))
    instruction.keys.append(AccountMeta(random_account, is_signer=False, is_writable=False))
    return [instruction]


# # 🥭 build_serum_settle_instructions function
#
# Creates a 'settle' instruction.
#

def build_serum_settle_instructions(context: Context, wallet: Wallet, market: Market, open_orders_address: PublicKey, base_token_account_address: PublicKey, quote_token_account_address: PublicKey) -> typing.Sequence[TransactionInstruction]:
    vault_signer = PublicKey.create_program_address(
        [bytes(market.state.public_key()), market.state.vault_signer_nonce().to_bytes(8, byteorder="little")],
        market.state.program_id(),
    )
    instruction = settle_funds(
        SettleFundsParams(
            market=market.state.public_key(),
            open_orders=open_orders_address,
            owner=wallet.address,
            base_vault=market.state.base_vault(),
            quote_vault=market.state.quote_vault(),
            base_wallet=base_token_account_address,
            quote_wallet=quote_token_account_address,
            vault_signer=vault_signer,
            program_id=market.state.program_id(),
        )
    )

    return [instruction]


# # 🥭 build_cancel_perp_order_instruction function
#
# Builds the instructions necessary for cancelling a perp order.
#


def build_cancel_perp_order_instructions(context: Context, wallet: Wallet, margin_account: Account, perp_market: PerpMarket, order: Order) -> typing.Sequence[TransactionInstruction]:
    # { buy: 0, sell: 1 }
    raw_side: int = 1 if order.side == Side.SELL else 0

    # Accounts expected by this instruction:
    # 0. `[]` mangoGroupPk
    # 1. `[writable]` mangoAccountPk
    # 2. `[signer]` ownerPk
    # 3. `[writable]` perpMarketPk
    # 4. `[writable]` bidsPk
    # 5. `[writable]` asksPk
    # 6. `[writable]` eventQueuePk

    return [
        TransactionInstruction(
            keys=[
                AccountMeta(is_signer=False, is_writable=False, pubkey=perp_market.group.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=margin_account.address),
                AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market.bids),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market.asks),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market.event_queue)
            ],
            program_id=context.program_id,
            data=layouts.CANCEL_PERP_ORDER.build(
                {
                    "order_id": order.id,
                    "side": raw_side
                })
        )
    ]


def build_place_perp_order_instructions(context: Context, wallet: Wallet, group: Group, margin_account: Account, perp_market: PerpMarket, price: Decimal, quantity: Decimal, client_order_id: int, side: Side, order_type: OrderType) -> typing.Sequence[TransactionInstruction]:
    # { buy: 0, sell: 1 }
    raw_side: int = 1 if side == Side.SELL else 0
    # { limit: 0, ioc: 1, postOnly: 2 }
    raw_order_type: int = 2 if order_type == OrderType.POST_ONLY else 1 if order_type == OrderType.IOC else 0

    base_decimals = perp_market.base_token.decimals
    quote_decimals = perp_market.quote_token.decimals

    base_factor = Decimal(10) ** base_decimals
    quote_factor = Decimal(10) ** quote_decimals

    native_price = ((price * quote_factor) * perp_market.contract_size) / (perp_market.quote_lot_size * base_factor)
    native_quantity = (quantity * base_factor) / perp_market.contract_size

    # /// Accounts expected by this instruction (6):
    # /// 0. `[]` mango_group_ai - TODO
    # /// 1. `[writable]` mango_account_ai - TODO
    # /// 2. `[signer]` owner_ai - TODO
    # /// 3. `[]` mango_cache_ai - TODO
    # /// 4. `[writable]` perp_market_ai - TODO
    # /// 5. `[writable]` bids_ai - TODO
    # /// 6. `[writable]` asks_ai - TODO
    # /// 7. `[writable]` event_queue_ai - TODO

    return [
        TransactionInstruction(
            keys=[
                AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=margin_account.address),
                AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
                AccountMeta(is_signer=False, is_writable=False, pubkey=group.cache),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market.bids),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market.asks),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market.event_queue),
                *list([AccountMeta(is_signer=False, is_writable=False,
                                   pubkey=oo_address or SYSTEM_PROGRAM_ADDRESS) for oo_address in margin_account.spot_open_orders])
            ],
            program_id=context.program_id,
            data=layouts.PLACE_PERP_ORDER.build(
                {
                    "price": native_price,
                    "quantity": native_quantity,
                    "client_order_id": client_order_id,
                    "side": raw_side,
                    "order_type": raw_order_type
                })
        )
    ]


def build_create_account_instructions(context: Context, wallet: Wallet, group: Group, new_account: SolanaAccount) -> typing.Sequence[TransactionInstruction]:
    mango_account_address = new_account.public_key()

    minimum_balance_response = context.client.get_minimum_balance_for_rent_exemption(layouts.MANGO_ACCOUNT.sizeof())
    minimum_balance = context.unwrap_or_raise_exception(minimum_balance_response)
    create = create_account(
        CreateAccountParams(wallet.address, mango_account_address, minimum_balance, layouts.MANGO_ACCOUNT.sizeof(), context.program_id))
    # /// 0. `[]` mango_group_ai - Group that this mango account is for
    # /// 1. `[writable]` mango_account_ai - the mango account data
    # /// 2. `[signer]` owner_ai - Solana account of owner of the mango account
    # /// 3. `[]` rent_ai - Rent sysvar account
    init = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=mango_account_address),
            AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=SYSVAR_CLOCK_PUBKEY)
        ],
        program_id=context.program_id,
        data=layouts.INIT_MANGO_ACCOUNT.build({})
    )
    return [create, init]


# /// Withdraw funds that were deposited earlier.
# ///
# /// Accounts expected by this instruction (10):
# ///
# /// 0. `[read]` mango_group_ai,   -
# /// 1. `[write]` mango_account_ai, -
# /// 2. `[read]` owner_ai,         -
# /// 3. `[read]` mango_cache_ai,   -
# /// 4. `[read]` root_bank_ai,     -
# /// 5. `[write]` node_bank_ai,     -
# /// 6. `[write]` vault_ai,         -
# /// 7. `[write]` token_account_ai, -
# /// 8. `[read]` signer_ai,        -
# /// 9. `[read]` token_prog_ai,    -
# /// 10. `[read]` clock_ai,         -
# /// 11..+ `[]` open_orders_accs - open orders for each of the spot market
# Withdraw {
#     quantity: u64,
#     allow_borrow: bool,
# },
def build_withdraw_instructions(context: Context, wallet: Wallet, group: Group, margin_account: Account, root_bank: RootBank, node_bank: NodeBank, token_account: TokenAccount, allow_borrow: bool) -> typing.Sequence[TransactionInstruction]:
    value = token_account.value.shift_to_native().value
    withdraw = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=margin_account.address),
            AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.cache),
            AccountMeta(is_signer=False, is_writable=False, pubkey=root_bank.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=node_bank.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=node_bank.vault),
            AccountMeta(is_signer=False, is_writable=True, pubkey=token_account.address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.signer_key),
            AccountMeta(is_signer=False, is_writable=False, pubkey=TOKEN_PROGRAM_ID),
            AccountMeta(is_signer=False, is_writable=False, pubkey=SYSVAR_CLOCK_PUBKEY),
            # *list([AccountMeta(is_signer=False, is_writable=False,
            #                    pubkey=oo_address or SYSTEM_PROGRAM_ADDRESS) for oo_address in margin_account.spot_open_orders])
        ],
        program_id=context.program_id,
        data=layouts.WITHDRAW_V3.build({
            "quantity": value,
            "allow_borrow": allow_borrow
        })
    )
    return [withdraw]
