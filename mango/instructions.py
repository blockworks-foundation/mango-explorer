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


import pyserum.enums
import typing

from decimal import Decimal
from pyserum.enums import OrderType as SerumOrderType, Side as SerumSide
from pyserum.instructions import ConsumeEventsParams, consume_events, settle_funds, SettleFundsParams
from pyserum.market import Market
from pyserum.open_orders_account import make_create_account_instruction
from solana.account import Account as SolanaAccount
from solana.publickey import PublicKey
from solana.system_program import CreateAccountParams, create_account
from solana.sysvar import SYSVAR_RENT_PUBKEY
from solana.transaction import AccountMeta, TransactionInstruction
from spl.token.constants import ACCOUNT_LEN, TOKEN_PROGRAM_ID
from spl.token.instructions import CloseAccountParams, InitializeAccountParams, Transfer2Params, close_account, create_associated_token_account, initialize_account, transfer2

from .account import Account
from .combinableinstructions import CombinableInstructions
from .constants import SYSTEM_PROGRAM_ADDRESS
from .context import Context
from .group import Group
from .layouts import layouts
from .orders import Order, OrderType, Side
from .perpmarketdetails import PerpMarketDetails
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
# Solana is that these functions *all return a combinable of instructions and signers*.
#
# It's likely that some operations will require actions split across multiple instructions because of
# instruction size limitiations, so all our functions are prepared for this without having to change
# the function signature in future.
#

# # 🥭 build_create_solana_account_instructions function
#
# Creates and initializes an SPL token account. Can add additional lamports too but that's usually not
# necesary.
#

def build_create_solana_account_instructions(context: Context, wallet: Wallet, program_id: PublicKey, size: int, lamports: int = 0) -> CombinableInstructions:
    minimum_balance_response = context.client.get_minimum_balance_for_rent_exemption(
        size, commitment=context.commitment)
    minimum_balance = context.unwrap_or_raise_exception(minimum_balance_response)
    account = SolanaAccount()
    create_instruction = create_account(
        CreateAccountParams(wallet.address, account.public_key(), lamports + minimum_balance, size, program_id))
    return CombinableInstructions(signers=[account], instructions=[create_instruction])


# # 🥭 build_create_spl_account_instructions function
#
# Creates and initializes an SPL token account. Can add additional lamports too but that's usually not
# necesary.
#
# Prefer `build_create_spl_account_instructions()` over this function. This function should be
# reserved for cases where you specifically don't want the associated token account.
#

def build_create_spl_account_instructions(context: Context, wallet: Wallet, token: Token, lamports: int = 0) -> CombinableInstructions:
    create_account_instructions = build_create_solana_account_instructions(
        context, wallet, TOKEN_PROGRAM_ID, ACCOUNT_LEN, lamports)
    initialize_instruction = initialize_account(InitializeAccountParams(
        TOKEN_PROGRAM_ID, create_account_instructions.signers[0].public_key(), token.mint, wallet.address))
    return create_account_instructions + CombinableInstructions(signers=[], instructions=[initialize_instruction])


# # 🥭 build_create_associated_spl_account_instructions function
#
# Creates and initializes an 'associated' SPL token account. This is the usual way of creating a
# token account now. `build_create_spl_account_instructions()` should be reserved for cases where
# you specifically don't want the associated token account.
#

def build_create_associated_spl_account_instructions(context: Context, wallet: Wallet, token: Token) -> CombinableInstructions:
    create_account_instructions = create_associated_token_account(wallet.address, wallet.address, token.mint)
    return CombinableInstructions(signers=[], instructions=[create_account_instructions])


# # 🥭 build_transfer_spl_tokens_instructions function
#
# Creates an instruction to transfer SPL tokens from one account to another.
#

def build_transfer_spl_tokens_instructions(context: Context, wallet: Wallet, token: Token, source: PublicKey, destination: PublicKey, quantity: Decimal) -> CombinableInstructions:
    amount = int(quantity * (10 ** token.decimals))
    instructions = [transfer2(Transfer2Params(TOKEN_PROGRAM_ID, source, token.mint,
                              destination, wallet.address, amount, int(token.decimals)))]
    return CombinableInstructions(signers=[], instructions=instructions)


# # 🥭 build_close_spl_account_instructions function
#
# Creates an instructio to close an SPL token account and transfers any remaining lamports to the wallet.
#

def build_close_spl_account_instructions(context: Context, wallet: Wallet, address: PublicKey) -> CombinableInstructions:
    return CombinableInstructions(signers=[], instructions=[close_account(CloseAccountParams(TOKEN_PROGRAM_ID, address, wallet.address, wallet.address))])


# # 🥭 build_create_serum_open_orders_instructions function
#
# Creates a Serum openorders-creating instruction.
#

def build_create_serum_open_orders_instructions(context: Context, wallet: Wallet, market: Market) -> CombinableInstructions:
    new_open_orders_account = SolanaAccount()
    response = context.client.get_minimum_balance_for_rent_exemption(
        layouts.OPEN_ORDERS.sizeof(), commitment=context.commitment)
    balanced_needed = context.unwrap_or_raise_exception(response)
    instruction = make_create_account_instruction(
        owner_address=wallet.address,
        new_account_address=new_open_orders_account.public_key(),
        lamports=balanced_needed,
        program_id=market.state.program_id(),
    )

    return CombinableInstructions(signers=[new_open_orders_account], instructions=[instruction])


# # 🥭 build_serum_place_order_instructions function
#
# Creates a Serum order-placing instruction using V3 of the NewOrder instruction.
#

def build_serum_place_order_instructions(context: Context, wallet: Wallet, market: Market, source: PublicKey, open_orders_address: PublicKey, order_type: OrderType, side: Side, price: Decimal, quantity: Decimal, client_id: int, fee_discount_address: typing.Optional[PublicKey]) -> CombinableInstructions:
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

    return CombinableInstructions(signers=[], instructions=[instruction])


# # 🥭 build_serum_consume_events_instructions function
#
# Creates an event-consuming 'crank' instruction.
#

def build_serum_consume_events_instructions(context: Context, market_address: PublicKey, event_queue_address: PublicKey, open_orders_addresses: typing.Sequence[PublicKey], limit: int = 32) -> CombinableInstructions:
    instruction = consume_events(ConsumeEventsParams(
        market=market_address,
        event_queue=event_queue_address,
        open_orders_accounts=open_orders_addresses,
        program_id=context.dex_program_id,
        limit=limit
    ))

    # The interface accepts (and currently requires) two accounts at the end, but
    # it doesn't actually use them.
    random_account = SolanaAccount().public_key()
    instruction.keys.append(AccountMeta(random_account, is_signer=False, is_writable=False))
    instruction.keys.append(AccountMeta(random_account, is_signer=False, is_writable=False))
    return CombinableInstructions(signers=[], instructions=[instruction])


# # 🥭 build_serum_settle_instructions function
#
# Creates a 'settle' instruction.
#

def build_serum_settle_instructions(context: Context, wallet: Wallet, market: Market, open_orders_address: PublicKey, base_token_account_address: PublicKey, quote_token_account_address: PublicKey) -> CombinableInstructions:
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

    return CombinableInstructions(signers=[], instructions=[instruction])

# # 🥭 build_spot_settle_instructions function
#
# Creates a 'settle' instruction for spot markets.
#
# /// Settle all funds from serum dex open orders
# ///
# /// Accounts expected by this instruction (18):
# ///
# /// 0. `[]` mango_group_ai - MangoGroup that this mango account is for
# /// 1. `[]` mango_cache_ai - MangoCache for this MangoGroup
# /// 2. `[signer]` owner_ai - MangoAccount owner
# /// 3. `[writable]` mango_account_ai - MangoAccount
# /// 4. `[]` dex_prog_ai - program id of serum dex
# /// 5.  `[writable]` spot_market_ai - dex MarketState account
# /// 6.  `[writable]` open_orders_ai - open orders for this market for this MangoAccount
# /// 7. `[]` signer_ai - MangoGroup signer key
# /// 8. `[writable]` dex_base_ai - base vault for dex MarketState
# /// 9. `[writable]` dex_quote_ai - quote vault for dex MarketState
# /// 10. `[]` base_root_bank_ai - MangoGroup base vault acc
# /// 11. `[writable]` base_node_bank_ai - MangoGroup quote vault acc
# /// 12. `[]` quote_root_bank_ai - MangoGroup quote vault acc
# /// 13. `[writable]` quote_node_bank_ai - MangoGroup quote vault acc
# /// 14. `[writable]` base_vault_ai - MangoGroup base vault acc
# /// 15. `[writable]` quote_vault_ai - MangoGroup quote vault acc
# /// 16. `[]` dex_signer_ai - dex Market signer account
# /// 17. `[]` spl token program


def build_spot_settle_instructions(context: Context, wallet: Wallet, account: Account,
                                   market: Market, group: Group, open_orders_address: PublicKey,
                                   base_rootbank: RootBank, base_nodebank: NodeBank,
                                   quote_rootbank: RootBank, quote_nodebank: NodeBank) -> CombinableInstructions:
    vault_signer = PublicKey.create_program_address(
        [bytes(market.state.public_key()), market.state.vault_signer_nonce().to_bytes(8, byteorder="little")],
        market.state.program_id(),
    )

    settle_instruction = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=group.cache),
            AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=account.address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=context.dex_program_id),
            AccountMeta(is_signer=False, is_writable=True, pubkey=market.state.public_key()),
            AccountMeta(is_signer=False, is_writable=True, pubkey=open_orders_address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.signer_key),
            AccountMeta(is_signer=False, is_writable=True, pubkey=market.state.base_vault()),
            AccountMeta(is_signer=False, is_writable=True, pubkey=market.state.quote_vault()),
            AccountMeta(is_signer=False, is_writable=False, pubkey=base_rootbank.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=base_nodebank.address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=quote_rootbank.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=quote_nodebank.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=base_nodebank.vault),
            AccountMeta(is_signer=False, is_writable=True, pubkey=quote_nodebank.vault),
            AccountMeta(is_signer=False, is_writable=False, pubkey=vault_signer),
            AccountMeta(is_signer=False, is_writable=False, pubkey=TOKEN_PROGRAM_ID)
        ],
        program_id=context.program_id,
        data=layouts.SETTLE_FUNDS.build(dict())
    )

    return CombinableInstructions(signers=[], instructions=[settle_instruction])


# # 🥭 build_compound_serum_place_order_instructions function
#
# This function puts a trade on the Serum orderbook and then cranks and settles.
# It follows the pattern described here:
#   https://solanadev.blogspot.com/2021/05/order-techniques-with-project-serum.html
#
# Here's an example (Raydium?) transaction that does this:
#   https://solanabeach.io/transaction/3Hb2h7QMM3BbJCK42BUDuVEYwwaiqfp2oQUZMDJvUuoyCRJD5oBmA3B8oAGkB9McdCFtwdT2VrSKM2GCKhJ92FpY
#
# Basically, it tries to send to a 'buy/sell' and settle all in one transaction.
#
# It does this by:
# * Sending a Place Order (V3) instruction
# * Sending a Consume Events (crank) instruction
# * Sending a Settle Funds instruction
# all in the same transaction. With V3 Serum, this should consistently settle funds to the wallet
# immediately if the order is filled (either because it's IOC or because it matches an order on the
# orderbook).
#

def build_compound_serum_place_order_instructions(context: Context, wallet: Wallet, market: Market, source: PublicKey, open_orders_address: PublicKey, all_open_orders_addresses: typing.Sequence[PublicKey], order_type: OrderType, side: Side, price: Decimal, quantity: Decimal, client_id: int, base_token_account_address: PublicKey, quote_token_account_address: PublicKey, fee_discount_address: typing.Optional[PublicKey], consume_limit: int = 32) -> CombinableInstructions:
    place_order = build_serum_place_order_instructions(
        context, wallet, market, source, open_orders_address, order_type, side, price, quantity, client_id, fee_discount_address)
    consume_events = build_serum_consume_events_instructions(
        context, market.state.public_key(), market.state.event_queue(), all_open_orders_addresses, consume_limit)
    settle = build_serum_settle_instructions(
        context, wallet, market, open_orders_address, base_token_account_address, quote_token_account_address)

    return place_order + consume_events + settle


# # 🥭 build_cancel_perp_order_instruction function
#
# Builds the instructions necessary for cancelling a perp order.
#


def build_cancel_perp_order_instructions(context: Context, wallet: Wallet, account: Account, perp_market_details: PerpMarketDetails, order: Order) -> CombinableInstructions:
    # Prefer cancelling by client ID so we don't have to keep track of the order side.
    if order.client_id != 0:
        data: bytes = layouts.CANCEL_PERP_ORDER_BY_CLIENT_ID.build(
            {
                "client_order_id": order.client_id
            })
    else:
        # { buy: 0, sell: 1 }
        raw_side: int = 1 if order.side == Side.SELL else 0
        data = layouts.CANCEL_PERP_ORDER.build(
            {
                "order_id": order.id,
                "side": raw_side
            })

    # Accounts expected by this instruction (both CANCEL_PERP_ORDER and CANCEL_PERP_ORDER_BY_CLIENT_ID are the same):
    # { isSigner: false, isWritable: false, pubkey: mangoGroupPk },
    # { isSigner: false, isWritable: true, pubkey: mangoAccountPk },
    # { isSigner: true, isWritable: false, pubkey: ownerPk },
    # { isSigner: false, isWritable: true, pubkey: perpMarketPk },
    # { isSigner: false, isWritable: true, pubkey: bidsPk },
    # { isSigner: false, isWritable: true, pubkey: asksPk },

    instructions = [
        TransactionInstruction(
            keys=[
                AccountMeta(is_signer=False, is_writable=False, pubkey=account.group.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=account.address),
                AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market_details.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market_details.bids),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market_details.asks)
            ],
            program_id=context.program_id,
            data=data
        )
    ]
    return CombinableInstructions(signers=[], instructions=instructions)


def build_place_perp_order_instructions(context: Context, wallet: Wallet, group: Group, account: Account, perp_market_details: PerpMarketDetails, price: Decimal, quantity: Decimal, client_order_id: int, side: Side, order_type: OrderType) -> CombinableInstructions:
    # { buy: 0, sell: 1 }
    raw_side: int = 1 if side == Side.SELL else 0
    # { limit: 0, ioc: 1, postOnly: 2 }
    raw_order_type: int = 2 if order_type == OrderType.POST_ONLY else 1 if order_type == OrderType.IOC else 0

    base_decimals = perp_market_details.base_token.decimals
    quote_decimals = perp_market_details.quote_token.decimals

    base_factor = Decimal(10) ** base_decimals
    quote_factor = Decimal(10) ** quote_decimals

    native_price = ((price * quote_factor) * perp_market_details.base_lot_size) / \
        (perp_market_details.quote_lot_size * base_factor)
    native_quantity = (quantity * base_factor) / perp_market_details.base_lot_size

    # /// Accounts expected by this instruction (6):
    # /// 0. `[]` mango_group_ai - TODO
    # /// 1. `[writable]` mango_account_ai - TODO
    # /// 2. `[signer]` owner_ai - TODO
    # /// 3. `[]` mango_cache_ai - TODO
    # /// 4. `[writable]` perp_market_ai - TODO
    # /// 5. `[writable]` bids_ai - TODO
    # /// 6. `[writable]` asks_ai - TODO
    # /// 7. `[writable]` event_queue_ai - TODO

    instructions = [
        TransactionInstruction(
            keys=[
                AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=account.address),
                AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
                AccountMeta(is_signer=False, is_writable=False, pubkey=group.cache),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market_details.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market_details.bids),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market_details.asks),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market_details.event_queue),
                *list([AccountMeta(is_signer=False, is_writable=False,
                                   pubkey=oo_address or SYSTEM_PROGRAM_ADDRESS) for oo_address in account.spot_open_orders])
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
    return CombinableInstructions(signers=[], instructions=instructions)


def build_mango_consume_events_instructions(context: Context, group: Group, perp_market_details: PerpMarketDetails, account_addresses: typing.Sequence[PublicKey], limit: Decimal = Decimal(32)) -> CombinableInstructions:
    # Accounts expected by this instruction:
    # { isSigner: false, isWritable: false, pubkey: mangoGroupPk },
    # { isSigner: false, isWritable: false, pubkey: mangoCachePk },
    # { isSigner: false, isWritable: true, pubkey: perpMarketPk },
    # { isSigner: false, isWritable: true, pubkey: eventQueuePk },
    # ...mangoAccountPks.sort().map((pubkey) => ({
    #     isSigner: false,
    #     isWritable: true,
    #     pubkey,
    # })),

    instructions = [
        TransactionInstruction(
            keys=[
                AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
                AccountMeta(is_signer=False, is_writable=False, pubkey=group.cache),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market_details.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market_details.event_queue),
                *list([AccountMeta(is_signer=False, is_writable=True,
                                   pubkey=account_address) for account_address in account_addresses])
            ],
            program_id=context.program_id,
            data=layouts.CONSUME_EVENTS.build(
                {
                    "limit": limit,
                })
        )
    ]
    return CombinableInstructions(signers=[], instructions=instructions)


def build_create_account_instructions(context: Context, wallet: Wallet, group: Group) -> CombinableInstructions:
    create_account_instructions = build_create_solana_account_instructions(
        context, wallet, context.program_id, layouts.MANGO_ACCOUNT.sizeof())
    mango_account_address = create_account_instructions.signers[0].public_key()

    # /// 0. `[]` mango_group_ai - Group that this mango account is for
    # /// 1. `[writable]` mango_account_ai - the mango account data
    # /// 2. `[signer]` owner_ai - Solana account of owner of the mango account
    # /// 3. `[]` rent_ai - Rent sysvar account
    init = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=mango_account_address),
            AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address)
        ],
        program_id=context.program_id,
        data=layouts.INIT_MANGO_ACCOUNT.build({})
    )
    return create_account_instructions + CombinableInstructions(signers=[], instructions=[init])


# /// Deposit funds into mango account
# ///
# /// Accounts expected by this instruction (8):
# ///
# /// 0. `[]` mango_group_ai - MangoGroup that this mango account is for
# /// 1. `[writable]` mango_account_ai - the mango account for this user
# /// 2. `[signer]` owner_ai - Solana account of owner of the mango account
# /// 3. `[]` mango_cache_ai - MangoCache
# /// 4. `[]` root_bank_ai - RootBank owned by MangoGroup
# /// 5. `[writable]` node_bank_ai - NodeBank owned by RootBank
# /// 6. `[writable]` vault_ai - TokenAccount owned by MangoGroup
# /// 7. `[]` token_prog_ai - acc pointed to by SPL token program id
# /// 8. `[writable]` owner_token_account_ai - TokenAccount owned by user which will be sending the funds
# Deposit {
#     quantity: u64,
# },
def build_deposit_instructions(context: Context, wallet: Wallet, group: Group, account: Account, root_bank: RootBank, node_bank: NodeBank, token_account: TokenAccount) -> CombinableInstructions:
    value = token_account.value.shift_to_native().value
    deposit = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=account.address),
            AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.cache),
            AccountMeta(is_signer=False, is_writable=False, pubkey=root_bank.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=node_bank.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=node_bank.vault),
            AccountMeta(is_signer=False, is_writable=False, pubkey=TOKEN_PROGRAM_ID),
            AccountMeta(is_signer=False, is_writable=True, pubkey=token_account.address)
        ],
        program_id=context.program_id,
        data=layouts.DEPOSIT.build({
            "quantity": value
        })
    )

    return CombinableInstructions(signers=[], instructions=[deposit])


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


def build_withdraw_instructions(context: Context, wallet: Wallet, group: Group, account: Account, root_bank: RootBank, node_bank: NodeBank, token_account: TokenAccount, allow_borrow: bool) -> CombinableInstructions:
    value = token_account.value.shift_to_native().value
    withdraw = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=account.address),
            AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.cache),
            AccountMeta(is_signer=False, is_writable=False, pubkey=root_bank.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=node_bank.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=node_bank.vault),
            AccountMeta(is_signer=False, is_writable=True, pubkey=token_account.address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.signer_key),
            AccountMeta(is_signer=False, is_writable=False, pubkey=TOKEN_PROGRAM_ID),
            *list([AccountMeta(is_signer=False, is_writable=False,
                               pubkey=oo_address or SYSTEM_PROGRAM_ADDRESS) for oo_address in account.spot_open_orders])
        ],
        program_id=context.program_id,
        data=layouts.WITHDRAW.build({
            "quantity": value,
            "allow_borrow": allow_borrow
        })
    )

    return CombinableInstructions(signers=[], instructions=[withdraw])


# # 🥭 build_mango_place_order_instructions function
#
# Creates a Mango order-placing instruction using the Serum instruction as the inner instruction. Will create
# the necessary OpenOrders account if it doesn't already exist.
#
# /// Accounts expected by PLACE_SPOT_ORDER instruction (19+openorders):
# { isSigner: false, isWritable: false, pubkey: mangoGroupPk },
# { isSigner: false, isWritable: true, pubkey: mangoAccountPk },
# { isSigner: true, isWritable: false, pubkey: ownerPk },
# { isSigner: false, isWritable: false, pubkey: mangoCachePk },
# { isSigner: false, isWritable: false, pubkey: serumDexPk },
# { isSigner: false, isWritable: true, pubkey: spotMarketPk },
# { isSigner: false, isWritable: true, pubkey: bidsPk },
# { isSigner: false, isWritable: true, pubkey: asksPk },
# { isSigner: false, isWritable: true, pubkey: requestQueuePk },
# { isSigner: false, isWritable: true, pubkey: eventQueuePk },
# { isSigner: false, isWritable: true, pubkey: spotMktBaseVaultPk },
# { isSigner: false, isWritable: true, pubkey: spotMktQuoteVaultPk },
# { isSigner: false, isWritable: false, pubkey: rootBankPk },
# { isSigner: false, isWritable: true, pubkey: nodeBankPk },
# { isSigner: false, isWritable: true, pubkey: vaultPk },
# { isSigner: false, isWritable: false, pubkey: TOKEN_PROGRAM_ID },
# { isSigner: false, isWritable: false, pubkey: signerPk },
# { isSigner: false, isWritable: false, pubkey: SYSVAR_RENT_PUBKEY },
# { isSigner: false, isWritable: false, pubkey: msrmOrSrmVaultPk },
# ...openOrders.map(({ pubkey, isWritable }) => ({
#     isSigner: false,
#     isWritable,
#     pubkey,
# })),

def build_spot_place_order_instructions(context: Context, wallet: Wallet, group: Group, account: Account,
                                        market: Market,
                                        order_type: OrderType, side: Side, price: Decimal,
                                        quantity: Decimal, client_id: int,
                                        fee_discount_address: typing.Optional[PublicKey]) -> CombinableInstructions:
    instructions: CombinableInstructions = CombinableInstructions.empty()

    spot_market_address = market.state.public_key()
    market_index = group.find_spot_market_index(spot_market_address)

    open_orders_address = account.spot_open_orders[market_index]
    if open_orders_address is None:
        create_open_orders = build_create_solana_account_instructions(
            context, wallet, context.dex_program_id, layouts.OPEN_ORDERS.sizeof())
        instructions += create_open_orders

        open_orders_address = create_open_orders.signers[0].public_key()

        # This line is a little nasty. Now that we know we have an OpenOrders account at this address, update
        # the Account so that future uses (like later in this method) have access to it in the right place.
        account.spot_open_orders[market_index] = open_orders_address

        initialise_open_orders_instruction = TransactionInstruction(
            keys=[
                AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=account.address),
                AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
                AccountMeta(is_signer=False, is_writable=False, pubkey=context.dex_program_id),
                AccountMeta(is_signer=False, is_writable=True, pubkey=open_orders_address),
                AccountMeta(is_signer=False, is_writable=False, pubkey=market.state.public_key()),
                AccountMeta(is_signer=False, is_writable=False, pubkey=group.signer_key),
                AccountMeta(is_signer=False, is_writable=False, pubkey=SYSVAR_RENT_PUBKEY)
            ],
            program_id=context.program_id,
            data=layouts.INIT_SPOT_OPEN_ORDERS.build(dict())
        )
        instructions += CombinableInstructions(signers=[], instructions=[initialise_open_orders_instruction])

    serum_order_type = pyserum.enums.OrderType.POST_ONLY if order_type == OrderType.POST_ONLY else pyserum.enums.OrderType.IOC if order_type == OrderType.IOC else pyserum.enums.OrderType.LIMIT
    serum_side = pyserum.enums.Side.BUY if side == Side.BUY else pyserum.enums.Side.SELL
    intrinsic_price = market.state.price_number_to_lots(float(price))
    max_base_quantity = market.state.base_size_number_to_lots(float(quantity))
    max_quote_quantity = market.state.base_size_number_to_lots(
        float(quantity)) * market.state.quote_lot_size() * market.state.price_number_to_lots(float(price))

    base_token_infos = [
        token_info for token_info in group.base_tokens if token_info is not None and token_info.token.mint == market.state.base_mint()]
    if len(base_token_infos) != 1:
        raise Exception(
            f"Could not find base token info for group {group.address} - length was {len(base_token_infos)} when it should be 1.")
    base_token_info = base_token_infos[0]
    quote_token_info = group.shared_quote_token

    root_bank: RootBank = quote_token_info.root_bank if side == Side.BUY else base_token_info.root_bank
    node_bank: NodeBank = root_bank.pick_node_bank(context)

    fee_discount_address_meta: typing.List[AccountMeta] = []
    if fee_discount_address is not None:
        fee_discount_address_meta = [AccountMeta(is_signer=False, is_writable=False, pubkey=fee_discount_address)]
    place_spot_instruction = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=account.address),
            AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.cache),
            AccountMeta(is_signer=False, is_writable=False, pubkey=context.dex_program_id),
            AccountMeta(is_signer=False, is_writable=True, pubkey=market.state.public_key()),
            AccountMeta(is_signer=False, is_writable=True, pubkey=market.state.bids()),
            AccountMeta(is_signer=False, is_writable=True, pubkey=market.state.asks()),
            AccountMeta(is_signer=False, is_writable=True, pubkey=market.state.request_queue()),
            AccountMeta(is_signer=False, is_writable=True, pubkey=market.state.event_queue()),
            AccountMeta(is_signer=False, is_writable=True, pubkey=market.state.base_vault()),
            AccountMeta(is_signer=False, is_writable=True, pubkey=market.state.quote_vault()),
            AccountMeta(is_signer=False, is_writable=False, pubkey=root_bank.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=node_bank.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=node_bank.vault),
            AccountMeta(is_signer=False, is_writable=False, pubkey=TOKEN_PROGRAM_ID),
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.signer_key),
            AccountMeta(is_signer=False, is_writable=False, pubkey=SYSVAR_RENT_PUBKEY),
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.srm_vault or SYSTEM_PROGRAM_ADDRESS),
            *list([AccountMeta(is_signer=False, is_writable=(oo_address == open_orders_address),
                               pubkey=oo_address or SYSTEM_PROGRAM_ADDRESS) for oo_address in account.spot_open_orders]),
            *fee_discount_address_meta
        ],
        program_id=context.program_id,
        data=layouts.PLACE_SPOT_ORDER.build(
            dict(
                side=serum_side,
                limit_price=intrinsic_price,
                max_base_quantity=max_base_quantity,
                max_quote_quantity=max_quote_quantity,
                self_trade_behavior=pyserum.enums.SelfTradeBehavior.DECREMENT_TAKE,
                order_type=serum_order_type,
                client_id=client_id,
                limit=65535,
            )
        )
    )

    return instructions + CombinableInstructions(signers=[], instructions=[place_spot_instruction])


# # 🥭 build_cancel_spot_order_instruction function
#
# Builds the instructions necessary for cancelling a spot order.
#


def build_cancel_spot_order_instructions(context: Context, wallet: Wallet, group: Group, account: Account, market: Market, order: Order, open_orders_address: PublicKey) -> CombinableInstructions:
    # { buy: 0, sell: 1 }
    raw_side: int = 1 if order.side == Side.SELL else 0

    # Accounts expected by this instruction:
    # { isSigner: false, isWritable: false, pubkey: mangoGroupPk },
    # { isSigner: true, isWritable: false, pubkey: ownerPk },
    # { isSigner: false, isWritable: false, pubkey: mangoAccountPk },
    # { isSigner: false, isWritable: false, pubkey: dexProgramId },
    # { isSigner: false, isWritable: true, pubkey: spotMarketPk },
    # { isSigner: false, isWritable: true, pubkey: bidsPk },
    # { isSigner: false, isWritable: true, pubkey: asksPk },
    # { isSigner: false, isWritable: true, pubkey: openOrdersPk },
    # { isSigner: false, isWritable: false, pubkey: signerKey },
    # { isSigner: false, isWritable: true, pubkey: eventQueuePk },

    instructions = [
        TransactionInstruction(
            keys=[
                AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
                AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
                AccountMeta(is_signer=False, is_writable=False, pubkey=account.address),
                AccountMeta(is_signer=False, is_writable=False, pubkey=context.dex_program_id),
                AccountMeta(is_signer=False, is_writable=True, pubkey=market.state.public_key()),
                AccountMeta(is_signer=False, is_writable=True, pubkey=market.state.bids()),
                AccountMeta(is_signer=False, is_writable=True, pubkey=market.state.asks()),
                AccountMeta(is_signer=False, is_writable=True, pubkey=open_orders_address),
                AccountMeta(is_signer=False, is_writable=False, pubkey=group.signer_key),
                AccountMeta(is_signer=False, is_writable=True, pubkey=market.state.event_queue())
            ],
            program_id=context.program_id,
            data=layouts.CANCEL_SPOT_ORDER.build(
                {
                    "order_id": order.id,
                    "side": raw_side
                })
        )
    ]
    return CombinableInstructions(signers=[], instructions=instructions)

# # 🥭 build_mango_settle_instructions function
#
# Creates a 'settle' instruction for Mango accounts.
#


def build_mango_settle_instructions(context: Context, wallet: Wallet, market: Market, open_orders_address: PublicKey, base_token_account_address: PublicKey, quote_token_account_address: PublicKey) -> CombinableInstructions:
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

    return CombinableInstructions(signers=[], instructions=[instruction])
