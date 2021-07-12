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
from solana.sysvar import SYSVAR_CLOCK_PUBKEY, SYSVAR_RENT_PUBKEY
from solana.transaction import AccountMeta, Transaction, TransactionInstruction
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
# Solana is that these functions *all return a list of instructions and signers*.
#
# It's likely that some operations will require actions split across multiple instructions because of
# instruction size limitiations, so all our functions are prepared for this without having to change
# the function signature in future.
#

class InstructionData():
    def __init__(self, signers: typing.Sequence[SolanaAccount], instructions: typing.Sequence[TransactionInstruction]):
        self.signers: typing.Sequence[SolanaAccount] = signers
        self.instructions: typing.Sequence[TransactionInstruction] = instructions

    @staticmethod
    def empty() -> "InstructionData":
        return InstructionData(signers=[], instructions=[])

    @staticmethod
    def from_signers(signers: typing.Sequence[SolanaAccount]) -> "InstructionData":
        return InstructionData(signers=signers, instructions=[])

    @staticmethod
    def from_wallet(wallet: Wallet) -> "InstructionData":
        return InstructionData(signers=[wallet.account], instructions=[])

    @staticmethod
    def from_instruction(instruction: TransactionInstruction) -> "InstructionData":
        return InstructionData(signers=[], instructions=[instruction])

    def __add__(self, new_instruction_data: "InstructionData") -> "InstructionData":
        all_signers = [*self.signers, *new_instruction_data.signers]
        all_instructions = [*self.instructions, *new_instruction_data.instructions]
        return InstructionData(signers=all_signers, instructions=all_instructions)

    def execute(self, context: Context) -> typing.Any:
        transaction = Transaction()
        transaction.instructions.extend(self.instructions)
        response = context.client.send_transaction(transaction, *self.signers, opts=context.transaction_options)
        return context.unwrap_or_raise_exception(response)

    def execute_and_unwrap_transaction_id(self, context: Context) -> typing.Any:
        return typing.cast(str, self.execute(context))

    def __str__(self) -> str:
        report: typing.List[str] = []
        for index, signer in enumerate(self.signers):
            report += [f"Signer[{index}]: {signer}"]

        for index, instruction in enumerate(self.instructions):
            for index, key in enumerate(instruction.keys):
                report += [f"Key[{index}]: {key.pubkey} {key.is_signer: <5} {key.is_writable: <5}"]
            report += [f"Program ID: {instruction.program_id}"]
            report += ["Data: " + "".join("{:02x}".format(x) for x in instruction.data)]

        return "\n".join(report)

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 _ensure_openorders function
#
# Unlike most functions in this file, `_ensure_openorders()` returns a tuple, not just an `InstructionData`.
#
# The idea is: callers just want to know the OpenOrders address, but if it doesn't exist they may need to add
# the instructions and signers for its creation before they try to use it.
#
# This function will always return the proper OpenOrders address, and will also return the `InstructionData` to
# create it (which will be empty of signers and instructions if the OpenOrders already exists).
#


def _ensure_openorders(context: Context, wallet: Wallet, group: Group, account: Account, market: Market) -> typing.Tuple[PublicKey, InstructionData]:
    spot_market_address = market.state.public_key()
    market_index: int = -1
    for index, spot in enumerate(group.spot_markets):
        if spot is not None and spot.address == spot_market_address:
            market_index = index
    if market_index == -1:
        raise Exception(f"Could not find spot market {spot_market_address} in group {group.address}")

    open_orders_address = account.spot_open_orders[market_index]
    if open_orders_address is not None:
        return open_orders_address, InstructionData.empty()

    creation = build_create_solana_account_instructions(
        context, wallet, context.dex_program_id, layouts.OPEN_ORDERS.sizeof())

    open_orders_address = creation.signers[0].public_key()

    # This is maybe a little nasty - updating the existing structure with the new OO account.
    account.spot_open_orders[market_index] = open_orders_address

    return open_orders_address, creation


# # 🥭 build_create_solana_account_instructions function
#
# Creates and initializes an SPL token account. Can add additional lamports too but that's usually not
# necesary.
#

def build_create_solana_account_instructions(context: Context, wallet: Wallet, program_id: PublicKey, size: int, lamports: int = 0) -> InstructionData:
    minimum_balance_response = context.client.get_minimum_balance_for_rent_exemption(
        size, commitment=context.commitment)
    minimum_balance = context.unwrap_or_raise_exception(minimum_balance_response)
    account = SolanaAccount()
    create_instruction = create_account(
        CreateAccountParams(wallet.address, account.public_key(), lamports + minimum_balance, size, program_id))
    return InstructionData(signers=[account], instructions=[create_instruction])


# # 🥭 build_create_spl_account_instructions function
#
# Creates and initializes an SPL token account. Can add additional lamports too but that's usually not
# necesary.
#

def build_create_spl_account_instructions(context: Context, wallet: Wallet, token: Token, address: PublicKey, lamports: int = 0) -> InstructionData:
    create_instructions = build_create_solana_account_instructions(context, wallet, TOKEN_PROGRAM_ID, ACCOUNT_LEN,
                                                                   lamports)
    initialize_instruction = initialize_account(InitializeAccountParams(
        TOKEN_PROGRAM_ID, address, token.mint, wallet.address))
    return create_instructions + InstructionData(signers=[], instructions=[initialize_instruction])


# # 🥭 build_transfer_spl_tokens_instructions function
#
# Creates an instruction to transfer SPL tokens from one account to another.
#

def build_transfer_spl_tokens_instructions(context: Context, wallet: Wallet, token: Token, source: PublicKey, destination: PublicKey, quantity: Decimal) -> InstructionData:
    amount = int(quantity * (10 ** token.decimals))
    instructions = [transfer2(Transfer2Params(TOKEN_PROGRAM_ID, source, token.mint,
                              destination, wallet.address, amount, int(token.decimals)))]
    return InstructionData(signers=[], instructions=instructions)


# # 🥭 build_close_spl_account_instructions function
#
# Creates an instructio to close an SPL token account and transfers any remaining lamports to the wallet.
#

def build_close_spl_account_instructions(context: Context, wallet: Wallet, address: PublicKey) -> InstructionData:
    return InstructionData(signers=[], instructions=[close_account(CloseAccountParams(TOKEN_PROGRAM_ID, address, wallet.address, wallet.address))])


# # 🥭 build_create_serum_open_orders_instructions function
#
# Creates a Serum openorders-creating instruction.
#

def build_create_serum_open_orders_instructions(context: Context, wallet: Wallet, market: Market) -> InstructionData:
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

    return InstructionData(signers=[new_open_orders_account], instructions=[instruction])


# # 🥭 build_serum_place_order_instructions function
#
# Creates a Serum order-placing instruction using V3 of the NewOrder instruction.
#

def build_serum_place_order_instructions(context: Context, wallet: Wallet, market: Market, source: PublicKey, open_orders_address: PublicKey, order_type: OrderType, side: Side, price: Decimal, quantity: Decimal, client_id: int, fee_discount_address: typing.Optional[PublicKey]) -> InstructionData:
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

    return InstructionData(signers=[], instructions=[instruction])


# # 🥭 build_serum_consume_events_instructions function
#
# Creates an event-consuming 'crank' instruction.
#

def build_serum_consume_events_instructions(context: Context, wallet: Wallet, market: Market, open_orders_addresses: typing.Sequence[PublicKey], limit: int = 32) -> InstructionData:
    instruction = consume_events(ConsumeEventsParams(
        market=market.state.public_key(),
        event_queue=market.state.event_queue(),
        open_orders_accounts=open_orders_addresses,
        program_id=context.dex_program_id,
        limit=limit
    ))

    # The interface accepts (and currently requires) two accounts at the end, but
    # it doesn't actually use them.
    random_account = SolanaAccount().public_key()
    instruction.keys.append(AccountMeta(random_account, is_signer=False, is_writable=False))
    instruction.keys.append(AccountMeta(random_account, is_signer=False, is_writable=False))
    return InstructionData(signers=[], instructions=[instruction])


# # 🥭 build_serum_settle_instructions function
#
# Creates a 'settle' instruction.
#

def build_serum_settle_instructions(context: Context, wallet: Wallet, market: Market, open_orders_address: PublicKey, base_token_account_address: PublicKey, quote_token_account_address: PublicKey) -> InstructionData:
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

    return InstructionData(signers=[], instructions=[instruction])


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

def build_compound_serum_place_order_instructions(context: Context, wallet: Wallet, market: Market, source: PublicKey, open_orders_address: PublicKey, all_open_orders_addresses: typing.Sequence[PublicKey], order_type: OrderType, side: Side, price: Decimal, quantity: Decimal, client_id: int, base_token_account_address: PublicKey, quote_token_account_address: PublicKey, fee_discount_address: typing.Optional[PublicKey], consume_limit: int = 32) -> InstructionData:
    place_order = build_serum_place_order_instructions(
        context, wallet, market, source, open_orders_address, order_type, side, price, quantity, client_id, fee_discount_address)
    consume_events = build_serum_consume_events_instructions(
        context, wallet, market, all_open_orders_addresses, consume_limit)
    settle = build_serum_settle_instructions(
        context, wallet, market, open_orders_address, base_token_account_address, quote_token_account_address)

    return place_order + consume_events + settle


# # 🥭 build_cancel_perp_order_instruction function
#
# Builds the instructions necessary for cancelling a perp order.
#


def build_cancel_perp_order_instructions(context: Context, wallet: Wallet, margin_account: Account, perp_market: PerpMarket, order: Order) -> InstructionData:
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
    # 0. `[]` mangoGroupPk
    # 1. `[writable]` mangoAccountPk
    # 2. `[signer]` ownerPk
    # 3. `[writable]` perpMarketPk
    # 4. `[writable]` bidsPk
    # 5. `[writable]` asksPk
    # 6. `[writable]` eventQueuePk

    instructions = [
        TransactionInstruction(
            keys=[
                AccountMeta(is_signer=False, is_writable=False, pubkey=margin_account.group.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=margin_account.address),
                AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market.bids),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market.asks),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market.event_queue)
            ],
            program_id=context.program_id,
            data=data
        )
    ]
    return InstructionData(signers=[], instructions=instructions)


def build_place_perp_order_instructions(context: Context, wallet: Wallet, group: Group, margin_account: Account, perp_market: PerpMarket, price: Decimal, quantity: Decimal, client_order_id: int, side: Side, order_type: OrderType) -> InstructionData:
    # { buy: 0, sell: 1 }
    raw_side: int = 1 if side == Side.SELL else 0
    # { limit: 0, ioc: 1, postOnly: 2 }
    raw_order_type: int = 2 if order_type == OrderType.POST_ONLY else 1 if order_type == OrderType.IOC else 0

    base_decimals = perp_market.base_token.decimals
    quote_decimals = perp_market.quote_token.decimals

    base_factor = Decimal(10) ** base_decimals
    quote_factor = Decimal(10) ** quote_decimals

    native_price = ((price * quote_factor) * perp_market.base_lot_size) / (perp_market.quote_lot_size * base_factor)
    native_quantity = (quantity * base_factor) / perp_market.base_lot_size

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
    return InstructionData(signers=[], instructions=instructions)


def build_mango_consume_events_instructions(context: Context, wallet: Wallet, group: Group, account: Account, perp_market: PerpMarket, limit: Decimal = Decimal(32)) -> InstructionData:
    # Accounts expected by this instruction (6):
    # 0. `[]` mangoGroupPk
    # 1. `[]` perpMarketPk
    # 2. `[writable]` eventQueuePk
    # 3+ `[writable]` mangoAccountPks...

    instructions = [
        TransactionInstruction(
            keys=[
                AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market.event_queue),
                AccountMeta(is_signer=False, is_writable=True, pubkey=account.address)
            ],
            program_id=context.program_id,
            data=layouts.CONSUME_EVENTS.build(
                {
                    "limit": limit,
                })
        )
    ]
    return InstructionData(signers=[], instructions=instructions)


def build_create_account_instructions(context: Context, wallet: Wallet, group: Group) -> InstructionData:
    create_account_instructions = build_create_solana_account_instructions(
        context, wallet, context.program_id, layouts.MANGO_ACCOUNT)
    mango_account_address = create_account_instructions.signers[0].public_key()

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
    return create_account_instructions + InstructionData(signers=[], instructions=[init])


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
def build_withdraw_instructions(context: Context, wallet: Wallet, group: Group, margin_account: Account, root_bank: RootBank, node_bank: NodeBank, token_account: TokenAccount, allow_borrow: bool) -> InstructionData:
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
            *list([AccountMeta(is_signer=False, is_writable=False,
                               pubkey=oo_address or SYSTEM_PROGRAM_ADDRESS) for oo_address in margin_account.spot_open_orders])
        ],
        program_id=context.program_id,
        data=layouts.WITHDRAW.build({
            "quantity": value,
            "allow_borrow": allow_borrow
        })
    )

    return InstructionData(signers=[], instructions=[withdraw])


# # 🥭 build_mango_place_order_instructions function
#
# Creates a Mango order-placing instruction using the Serum instruction as the inner instruction.
#

def build_spot_place_order_instructions(context: Context, wallet: Wallet, group: Group, account: Account,
                                        market: Market,
                                        order_type: OrderType, side: Side, price: Decimal,
                                        quantity: Decimal, client_id: int,
                                        fee_discount_address: typing.Optional[PublicKey]) -> InstructionData:
    instructions: InstructionData = InstructionData.empty()

    open_orders_address, create_open_orders = _ensure_openorders(context, wallet, group, account, market)
    instructions += create_open_orders

    serum_order_type = pyserum.enums.OrderType.POST_ONLY if order_type == OrderType.POST_ONLY else pyserum.enums.OrderType.IOC if order_type == OrderType.IOC else pyserum.enums.OrderType.LIMIT
    serum_side = pyserum.enums.Side.BUY if side == Side.BUY else pyserum.enums.Side.SELL
    intrinsic_price = market.state.price_number_to_lots(float(price))
    max_base_quantity = market.state.base_size_number_to_lots(float(quantity))
    max_quote_quantity = market.state.base_size_number_to_lots(
        float(quantity)) * market.state.quote_lot_size() * market.state.price_number_to_lots(float(price))

    quote_token_info = group.shared_quote_token
    base_token_infos = [
        token_info for token_info in group.base_tokens if token_info is not None and token_info.token.mint == market.state.base_mint()]
    if len(base_token_infos) != 1:
        raise Exception(
            f"Could not find base token info for group {group.address} - length was {len(base_token_infos)} when it should be 1.")
    base_token_info = base_token_infos[0]

    vault_signer = PublicKey.create_program_address(
        [bytes(market.state.public_key()), market.state.vault_signer_nonce().to_bytes(8, byteorder="little")],
        market.state.program_id(),
    )

    base_node_bank = base_token_info.root_bank.pick_node_bank(context)
    quote_node_bank = quote_token_info.root_bank.pick_node_bank(context)

    # /// Accounts expected by this instruction (22+openorders):
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
    # { isSigner: false, isWritable: false, pubkey: baseRootBankPk },
    # { isSigner: false, isWritable: true, pubkey: baseNodeBankPk },
    # { isSigner: false, isWritable: true, pubkey: quoteRootBankPk },
    # { isSigner: false, isWritable: true, pubkey: quoteNodeBankPk },
    # { isSigner: false, isWritable: true, pubkey: quoteVaultPk },
    # { isSigner: false, isWritable: true, pubkey: baseVaultPk },
    # { isSigner: false, isWritable: false, pubkey: TOKEN_PROGRAM_ID },
    # { isSigner: false, isWritable: false, pubkey: signerPk },
    # { isSigner: false, isWritable: false, pubkey: SYSVAR_RENT_PUBKEY },
    # { isSigner: false, isWritable: false, pubkey: dexSignerPk },
    # ...openOrders.map((pubkey) => ({
    #   isSigner: false,
    #   isWritable: true, // TODO: only pass the one writable you are going to place the order on
    #   pubkey,
    # })),
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
            AccountMeta(is_signer=False, is_writable=False, pubkey=base_token_info.root_bank.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=base_node_bank.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=quote_token_info.root_bank.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=quote_node_bank.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=quote_node_bank.vault),
            AccountMeta(is_signer=False, is_writable=True, pubkey=base_node_bank.vault),
            AccountMeta(is_signer=False, is_writable=False, pubkey=TOKEN_PROGRAM_ID),
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.signer_key),
            AccountMeta(is_signer=False, is_writable=False, pubkey=SYSVAR_RENT_PUBKEY),
            AccountMeta(is_signer=False, is_writable=False, pubkey=vault_signer),
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

    return instructions + InstructionData(signers=[], instructions=[place_spot_instruction])


def build_compound_spot_place_order_instructions(context: Context, wallet: Wallet, group: Group, account: Account,
                                                 market: Market, source: PublicKey, order_type: OrderType,
                                                 side: Side, price: Decimal, quantity: Decimal, client_id: int,
                                                 fee_discount_address: typing.Optional[PublicKey]) -> InstructionData:
    _, create_open_orders = _ensure_openorders(context, wallet, group, account, market)

    place_order = build_spot_place_order_instructions(context, wallet, group, account, market, order_type,
                                                      side, price, quantity, client_id, fee_discount_address)

    open_orders_addresses = list([oo for oo in account.spot_open_orders if oo is not None])

    consume_events = build_serum_consume_events_instructions(context, wallet, market, open_orders_addresses)

    # quote_token_info = group.shared_quote_token
    # base_token_infos = [
    #     token_info for token_info in group.base_tokens if token_info is not None and token_info.token.mint == market.state.base_mint()]
    # if len(base_token_infos) != 1:
    #     raise Exception(
    #         f"Could not find base token info for group {group.address} - length was {len(base_token_infos)} when it should be 1.")
    # base_token_info = base_token_infos[0]
    # base_token_account = TokenAccount.fetch_largest_for_owner_and_token(context, wallet.address, base_token_info.token)
    # quote_token_account = TokenAccount.fetch_largest_for_owner_and_token(
    #     context, wallet.address, quote_token_info.token)

    # settle: InstructionData = InstructionData.empty()
    # if base_token_account is not None and quote_token_account is not None:
    #     open_order_accounts = market.find_open_orders_accounts_for_owner(wallet.address)
    #     settlement_open_orders = [oo for oo in open_order_accounts if oo.market == market.state.public_key()]
    #     if len(settlement_open_orders) > 0 and settlement_open_orders[0] is not None:
    #         settle = build_serum_settle_instructions(
    #             context, wallet, market, open_orders_address, base_token_account.address, quote_token_account.address)

    combined = create_open_orders + place_order + consume_events  # + settle
    return combined


# # 🥭 build_cancel_perp_order_instruction function
#
# Builds the instructions necessary for cancelling a perp order.
#


def build_cancel_spot_order_instructions(context: Context, wallet: Wallet, group: Group, account: Account, market: Market, order: Order, open_orders_address: PublicKey) -> InstructionData:
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
    return InstructionData(signers=[], instructions=instructions)
