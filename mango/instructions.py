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

from datetime import datetime
from decimal import Decimal
from pyserum._layouts.instructions import (
    INSTRUCTIONS_LAYOUT as PYSERUM_INSTRUCTIONS_LAYOUT,
    InstructionType as PySerumInstructionType,
)
from pyserum.enums import OrderType as PySerumOrderType, Side as PySerumSide
from pyserum.instructions import (
    settle_funds as pyserum_settle_funds,
    SettleFundsParams as PySerumSettleFundsParams,
)
from pyserum.market.market import Market as PySerumMarket
from pyserum.open_orders_account import (
    make_create_account_instruction as pyserum_make_create_account_instruction,
)
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.system_program import CreateAccountParams, create_account
from solana.transaction import AccountMeta, TransactionInstruction
from spl.token.constants import (
    ACCOUNT_LEN,
    TOKEN_PROGRAM_ID,
)
from spl.token.instructions import (
    CloseAccountParams,
    InitializeAccountParams,
    TransferParams,
    close_account,
    create_associated_token_account,
    initialize_account,
    transfer,
)

from .combinableinstructions import CombinableInstructions
from .constants import I64_MAX, SYSTEM_PROGRAM_ADDRESS
from .context import Context
from .layouts import layouts
from .orders import Order, OrderType, Side

from .perpmarketdetails import PerpMarketDetails

# from .spotmarket import SpotMarket
from .tokens import Token
from .tokenaccount import TokenAccount
from .tokenbank import TokenBank, NodeBank, RootBank
from .wallet import Wallet

# 🥭 Interfaces
#
# To avoid circular dependencies, here we specify the bare interfaces we need for some
# of the objects. For instance, where a function takes an IAccount, you can (and probably
# should) safely pass in an IAccount.
#


class IAccount(typing.Protocol):
    group_address: PublicKey

    @property
    def address(self) -> PublicKey:
        raise NotImplementedError(
            "IAccount.address is not implemented on the Protocol."
        )

    @property
    def spot_open_orders_by_index(self) -> typing.Sequence[typing.Optional[PublicKey]]:
        raise NotImplementedError(
            "IAccount.spot_open_orders_by_index is not implemented on the Protocol."
        )

    @property
    def spot_open_orders(self) -> typing.Sequence[PublicKey]:
        raise NotImplementedError(
            "IAccount.spot_open_orders is not implemented on the Protocol."
        )

    def update_spot_open_orders_for_market(
        self, spot_market_index: int, spot_open_orders: PublicKey
    ) -> None:
        raise NotImplementedError(
            "IAccount.update_spot_open_orders_for_market() is not implemented on the Protocol."
        )


class IGroupSlot(typing.Protocol):
    index: int


class IGroup(typing.Protocol):
    cache: PublicKey
    signer_key: PublicKey
    fees_vault: PublicKey
    shared_quote: TokenBank

    @property
    def address(self) -> PublicKey:
        raise NotImplementedError("IGroup.address is not implemented on the Protocol.")

    @property
    def tokens_by_index(self) -> typing.Sequence[typing.Optional[TokenBank]]:
        raise NotImplementedError(
            "IGroup.tokens_by_index is not implemented on the Protocol."
        )

    @property
    def base_tokens_by_index(self) -> typing.Sequence[typing.Optional[TokenBank]]:
        raise NotImplementedError(
            "IGroup.base_tokens_by_index is not implemented on the Protocol."
        )

    def slot_by_spot_market_address(self, spot_market_address: PublicKey) -> IGroupSlot:
        raise NotImplementedError(
            "IGroup.slot_by_spot_market_address() is not implemented on the Protocol."
        )


class IPerpMarket(typing.Protocol):
    underlying_perp_market: PerpMarketDetails

    @property
    def address(self) -> PublicKey:
        raise NotImplementedError(
            "IPerpMarket.address is not implemented on the Protocol."
        )


class ISpotMarket(typing.Protocol):
    underlying_serum_market: PySerumMarket

    @property
    def address(self) -> PublicKey:
        raise NotImplementedError(
            "ISpotMarket.address is not implemented on the Protocol."
        )

    @property
    def bids_address(self) -> PublicKey:
        raise NotImplementedError(
            "ISpotMarket.bids_address is not implemented on the Protocol."
        )

    @property
    def asks_address(self) -> PublicKey:
        raise NotImplementedError(
            "ISpotMarket.asks_address is not implemented on the Protocol."
        )

    @property
    def event_queue_address(self) -> PublicKey:
        raise NotImplementedError(
            "ISpotMarket.event_queue_address is not implemented on the Protocol."
        )


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

# #
# # 🥭 SOLANA instruction builders
# #

# # 🥭 build_solana_create_account_instructions function
#
# Creates and initializes an SPL token account. Can add additional lamports too but that's usually not
# necesary.
#
def build_solana_create_account_instructions(
    context: Context,
    wallet: Wallet,
    mango_program_address: PublicKey,
    size: int,
    lamports: int = 0,
) -> CombinableInstructions:
    minimum_balance = context.client.get_minimum_balance_for_rent_exemption(size)
    account = Keypair()
    create_instruction = create_account(
        CreateAccountParams(
            wallet.address,
            account.public_key,
            lamports + minimum_balance,
            size,
            mango_program_address,
        )
    )
    return CombinableInstructions(signers=[account], instructions=[create_instruction])


# #
# # 🥭 SPL instruction builders
# #


# # 🥭 build_spl_create_account_instructions function
#
# Creates and initializes an SPL token account. Can add additional lamports too but that's usually not
# necesary.
#
# Prefer `build_spl_create_account_instructions()` over this function. This function should be
# reserved for cases where you specifically don't want the associated token account.
#
def build_spl_create_account_instructions(
    context: Context, wallet: Wallet, token: Token, lamports: int = 0
) -> CombinableInstructions:
    create_account_instructions = build_solana_create_account_instructions(
        context, wallet, TOKEN_PROGRAM_ID, ACCOUNT_LEN, lamports
    )
    initialize_instruction = initialize_account(
        InitializeAccountParams(
            TOKEN_PROGRAM_ID,
            create_account_instructions.signers[0].public_key,
            token.mint,
            wallet.address,
        )
    )
    return create_account_instructions + CombinableInstructions(
        signers=[], instructions=[initialize_instruction]
    )


# # 🥭 build_spl_create_associated_account_instructions function
#
# Creates and initializes an 'associated' SPL token account. This is the usual way of creating a
# token account now. `build_spl_create_account_instructions()` should be reserved for cases where
# you specifically don't want the associated token account.
#
def build_spl_create_associated_account_instructions(
    context: Context, wallet: Wallet, owner: PublicKey, token: Token
) -> CombinableInstructions:
    create_account_instructions = create_associated_token_account(
        wallet.address, owner, token.mint
    )
    return CombinableInstructions(
        signers=[], instructions=[create_account_instructions]
    )


# # 🥭 build_spl_transfer_tokens_instructions function
#
# Creates an instruction to transfer SPL tokens from one account to another.
#
def build_spl_transfer_tokens_instructions(
    context: Context,
    wallet: Wallet,
    token: Token,
    source: PublicKey,
    destination: PublicKey,
    quantity: Decimal,
) -> CombinableInstructions:
    amount = int(token.shift_to_native(quantity))
    instructions = [
        transfer(
            TransferParams(
                TOKEN_PROGRAM_ID, source, destination, wallet.address, amount, []
            )
        )
    ]
    return CombinableInstructions(signers=[], instructions=instructions)


# # 🥭 build_spl_close_account_instructions function
#
# Creates an instructio to close an SPL token account and transfers any remaining lamports to the wallet.
#
def build_spl_close_account_instructions(
    context: Context, wallet: Wallet, address: PublicKey
) -> CombinableInstructions:
    return CombinableInstructions(
        signers=[],
        instructions=[
            close_account(
                CloseAccountParams(
                    TOKEN_PROGRAM_ID, address, wallet.address, wallet.address
                )
            )
        ],
    )


# # 🥭 build_spl_faucet_airdrop_instructions function
#
# Creates an airdrop instruction for compatible faucets (those based on https://github.com/paul-schaaf/spl-token-faucet)
#
def build_spl_faucet_airdrop_instructions(
    token_mint: PublicKey, destination: PublicKey, faucet: PublicKey, quantity: Decimal
) -> CombinableInstructions:
    faucet_program_address: PublicKey = PublicKey(
        "4bXpkKSV8swHSnwqtzuboGPaPDeEgAn4Vt8GfarV5rZt"
    )
    authority_and_nonce: typing.Tuple[PublicKey, int] = PublicKey.find_program_address(
        [b"faucet"], faucet_program_address
    )
    authority: PublicKey = authority_and_nonce[0]

    # Mints and airdrops tokens from a faucet.
    #
    # SPL instruction is at:
    #   https://github.com/paul-schaaf/spl-token-faucet/blob/main/src/program/src/instruction.rs
    #
    # ///
    # /// Mints Tokens
    # ///
    # /// 0. `[]` The mint authority - Program Derived Address
    # /// 1. `[writable]` Token Mint IAccount
    # /// 2. `[writable]` Destination IAccount
    # /// 3. `[]` The SPL Token Program
    # /// 4. `[]` The Faucet IAccount
    # /// 5. `[optional/signer]` Admin IAccount
    faucet_airdrop_instruction = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=authority),
            AccountMeta(is_signer=False, is_writable=True, pubkey=token_mint),
            AccountMeta(is_signer=False, is_writable=True, pubkey=destination),
            AccountMeta(is_signer=False, is_writable=False, pubkey=TOKEN_PROGRAM_ID),
            AccountMeta(is_signer=False, is_writable=False, pubkey=faucet),
        ],
        program_id=faucet_program_address,
        data=layouts.FAUCET_AIRDROP.build({"quantity": quantity}),
    )
    return CombinableInstructions(signers=[], instructions=[faucet_airdrop_instruction])


# #
# # 🥭 Serum instruction builders
# #


# # 🥭 build_serum_create_openorders_instructions function
#
# Creates a Serum openorders-creating instruction.
#
def build_serum_create_openorders_instructions(
    context: Context, wallet: Wallet, market: PySerumMarket
) -> CombinableInstructions:
    new_open_orders_account = Keypair()
    minimum_balance = context.client.get_minimum_balance_for_rent_exemption(
        layouts.OPEN_ORDERS.sizeof()
    )
    instruction = pyserum_make_create_account_instruction(
        owner_address=wallet.address,
        new_account_address=new_open_orders_account.public_key,
        lamports=minimum_balance,
        program_id=market.state.program_id(),
    )

    return CombinableInstructions(
        signers=[new_open_orders_account], instructions=[instruction]
    )


# # 🥭 build_serum_place_order_instructions function
#
# Creates a Serum order-placing instruction using V3 of the NewOrder instruction.
#
def build_serum_place_order_instructions(
    context: Context,
    wallet: Wallet,
    market: PySerumMarket,
    source: PublicKey,
    open_orders_address: PublicKey,
    order_type: OrderType,
    side: Side,
    price: Decimal,
    quantity: Decimal,
    client_id: int,
    fee_discount_address: PublicKey,
) -> CombinableInstructions:
    serum_order_type: PySerumOrderType = (
        PySerumOrderType.POST_ONLY
        if order_type == OrderType.POST_ONLY
        else PySerumOrderType.IOC
        if order_type == OrderType.IOC
        else PySerumOrderType.LIMIT
    )
    serum_side: PySerumSide = PySerumSide.SELL if side == Side.SELL else PySerumSide.BUY

    instruction = market.make_place_order_instruction(
        source,
        wallet.keypair,
        serum_order_type,
        serum_side,
        float(price),
        float(quantity),
        client_id,
        open_orders_address,
        fee_discount_address,
    )

    return CombinableInstructions(signers=[], instructions=[instruction])


# # 🥭 build_serum_consume_events_instructions function
#
# Creates an event-consuming 'crank' instruction.
#
def build_serum_consume_events_instructions(
    context: Context,
    market_address: PublicKey,
    event_queue_address: PublicKey,
    open_orders_addresses: typing.Sequence[PublicKey],
    limit: int = 32,
) -> CombinableInstructions:
    instruction = TransactionInstruction(
        keys=[
            AccountMeta(pubkey=pubkey, is_signer=False, is_writable=True)
            for pubkey in [*open_orders_addresses, market_address, event_queue_address]
        ],
        program_id=context.serum_program_address,
        data=PYSERUM_INSTRUCTIONS_LAYOUT.build(
            dict(
                instruction_type=PySerumInstructionType.CONSUME_EVENTS,
                args=dict(limit=limit),
            )
        ),
    )

    # The interface accepts (and currently requires) two accounts at the end, but
    # it doesn't actually use them.
    random_account = Keypair().public_key
    instruction.keys.append(
        AccountMeta(random_account, is_signer=False, is_writable=True)
    )
    instruction.keys.append(
        AccountMeta(random_account, is_signer=False, is_writable=True)
    )
    return CombinableInstructions(signers=[], instructions=[instruction])


# # 🥭 build_serum_settle_instructions function
#
# Creates a 'settle' instruction.
#
def build_serum_settle_instructions(
    context: Context,
    wallet: Wallet,
    market: PySerumMarket,
    open_orders_address: PublicKey,
    base_token_account_address: PublicKey,
    quote_token_account_address: PublicKey,
) -> CombinableInstructions:
    vault_signer = PublicKey.create_program_address(
        [
            bytes(market.state.public_key()),
            market.state.vault_signer_nonce().to_bytes(8, byteorder="little"),
        ],
        market.state.program_id(),
    )
    instruction = pyserum_settle_funds(
        PySerumSettleFundsParams(
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


# #
# # 🥭 Spot instruction builders
# #


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
# /// 16. `[]` dex_signer_ai - dex PySerumMarket signer account
# /// 17. `[]` spl token program
#
def build_spot_settle_instructions(
    context: Context,
    wallet: Wallet,
    account: IAccount,
    market: PySerumMarket,
    group: IGroup,
    open_orders_address: PublicKey,
    base_rootbank: RootBank,
    base_nodebank: NodeBank,
    quote_rootbank: RootBank,
    quote_nodebank: NodeBank,
) -> CombinableInstructions:
    vault_signer = PublicKey.create_program_address(
        [
            bytes(market.state.public_key()),
            market.state.vault_signer_nonce().to_bytes(8, byteorder="little"),
        ],
        market.state.program_id(),
    )

    settle_instruction = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=group.cache),
            AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=account.address),
            AccountMeta(
                is_signer=False, is_writable=False, pubkey=context.serum_program_address
            ),
            AccountMeta(
                is_signer=False, is_writable=True, pubkey=market.state.public_key()
            ),
            AccountMeta(is_signer=False, is_writable=True, pubkey=open_orders_address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.signer_key),
            AccountMeta(
                is_signer=False, is_writable=True, pubkey=market.state.base_vault()
            ),
            AccountMeta(
                is_signer=False, is_writable=True, pubkey=market.state.quote_vault()
            ),
            AccountMeta(
                is_signer=False, is_writable=False, pubkey=base_rootbank.address
            ),
            AccountMeta(
                is_signer=False, is_writable=True, pubkey=base_nodebank.address
            ),
            AccountMeta(
                is_signer=False, is_writable=False, pubkey=quote_rootbank.address
            ),
            AccountMeta(
                is_signer=False, is_writable=True, pubkey=quote_nodebank.address
            ),
            AccountMeta(is_signer=False, is_writable=True, pubkey=base_nodebank.vault),
            AccountMeta(is_signer=False, is_writable=True, pubkey=quote_nodebank.vault),
            AccountMeta(is_signer=False, is_writable=False, pubkey=vault_signer),
            AccountMeta(is_signer=False, is_writable=False, pubkey=TOKEN_PROGRAM_ID),
        ],
        program_id=context.mango_program_address,
        data=layouts.SETTLE_FUNDS.build({}),
    )

    return CombinableInstructions(signers=[], instructions=[settle_instruction])


def build_spot_create_openorders_instructions(
    context: Context,
    wallet: Wallet,
    group: IGroup,
    account: IAccount,
    spot_market: ISpotMarket,
    open_orders_address: PublicKey,
) -> CombinableInstructions:
    instructions: CombinableInstructions = CombinableInstructions.empty()

    # /// Accounts expected by this instruction (8):
    # ///
    # /// 0. `[]` mango_group_ai - MangoGroup that this mango account is for
    # /// 1. `[writable]` mango_account_ai - MangoAccount
    # /// 2. `[signer]` owner_ai - MangoAccount owner
    # /// 3. `[]` dex_prog_ai - program id of serum dex
    # /// 4. `[writable]` open_orders_ai - open orders PDA
    # /// 5. `[]` spot_market_ai - dex MarketState account
    # /// 6. `[]` signer_ai - IGroup Signer IAccount
    # /// 7. `[]` system_prog_ai - System program
    create_open_orders_instruction = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=account.address),
            AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
            AccountMeta(
                is_signer=False, is_writable=False, pubkey=context.serum_program_address
            ),
            AccountMeta(is_signer=False, is_writable=True, pubkey=open_orders_address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=spot_market.address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.signer_key),
            AccountMeta(
                is_signer=False, is_writable=False, pubkey=SYSTEM_PROGRAM_ADDRESS
            ),
        ],
        program_id=context.mango_program_address,
        data=layouts.CREATE_SPOT_OPEN_ORDERS.build({}),
    )
    instructions += CombinableInstructions(
        signers=[], instructions=[create_open_orders_instruction]
    )
    return instructions


# # 🥭 build_spot_place_order_instructions function
#
# Creates a Mango order-placing instruction using the Serum instruction as the inner instruction. Will create
# the necessary OpenOrders account if it doesn't already exist.
#
# /// Accounts expected by PLACE_SPOT_ORDER_2 instruction (22+openorders):
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
# { isSigner: false, isWritable: true, pubkey: baseVaultPk },
# { isSigner: false, isWritable: false, pubkey: quoteRootBankPk },
# { isSigner: false, isWritable: true, pubkey: quoteNodeBankPk },
# { isSigner: false, isWritable: true, pubkey: quoteVaultPk },
# { isSigner: false, isWritable: false, pubkey: TOKEN_PROGRAM_ID },
# { isSigner: false, isWritable: false, pubkey: signerPk },
# { isSigner: false, isWritable: false, pubkey: dexSignerPk },
# { isSigner: false, isWritable: false, pubkey: msrmOrSrmVaultPk },
# ...openOrders.map(({ pubkey, isWritable }) => ({
#   isSigner: false,
#   isWritable,
#   pubkey,
# })),
def build_spot_place_order_instructions(
    context: Context,
    wallet: Wallet,
    group: IGroup,
    account: IAccount,
    spot_market: ISpotMarket,
    open_orders_address: PublicKey,
    order_type: OrderType,
    side: Side,
    price: Decimal,
    quantity: Decimal,
    client_id: int,
    fee_discount_address: PublicKey,
) -> CombinableInstructions:
    instructions: CombinableInstructions = CombinableInstructions.empty()

    pyserum_market: PySerumMarket = spot_market.underlying_serum_market
    serum_order_type: pyserum.enums.OrderType = order_type.to_serum()
    serum_side: pyserum.enums.Side = side.to_serum()
    intrinsic_price = pyserum_market.state.price_number_to_lots(float(price))
    max_base_quantity = pyserum_market.state.base_size_number_to_lots(float(quantity))
    max_quote_quantity = (
        pyserum_market.state.base_size_number_to_lots(float(quantity))
        * pyserum_market.state.quote_lot_size()
        * pyserum_market.state.price_number_to_lots(float(price))
    )

    base_token_banks = [
        token_bank
        for token_bank in group.base_tokens_by_index
        if token_bank is not None
        and token_bank.token.mint == pyserum_market.state.base_mint()
    ]
    if len(base_token_banks) != 1:
        raise Exception(
            f"Could not find base token info for group {group.address} - length was {len(base_token_banks)} when it should be 1."
        )
    base_token_bank = base_token_banks[0]
    quote_token_bank = group.shared_quote

    base_root_bank: RootBank = base_token_bank.ensure_root_bank(context)
    base_node_bank: NodeBank = base_root_bank.pick_node_bank(context)
    quote_root_bank: RootBank = quote_token_bank.ensure_root_bank(context)
    quote_node_bank: NodeBank = quote_root_bank.pick_node_bank(context)

    vault_signer = PublicKey.create_program_address(
        [
            bytes(spot_market.address),
            pyserum_market.state.vault_signer_nonce().to_bytes(8, byteorder="little"),
        ],
        pyserum_market.state.program_id(),
    )

    place_spot_instruction = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=account.address),
            AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.cache),
            AccountMeta(
                is_signer=False, is_writable=False, pubkey=context.serum_program_address
            ),
            AccountMeta(is_signer=False, is_writable=True, pubkey=spot_market.address),
            AccountMeta(
                is_signer=False, is_writable=True, pubkey=spot_market.bids_address
            ),
            AccountMeta(
                is_signer=False, is_writable=True, pubkey=spot_market.asks_address
            ),
            AccountMeta(
                is_signer=False,
                is_writable=True,
                pubkey=pyserum_market.state.request_queue(),
            ),
            AccountMeta(
                is_signer=False,
                is_writable=True,
                pubkey=spot_market.event_queue_address,
            ),
            AccountMeta(
                is_signer=False,
                is_writable=True,
                pubkey=pyserum_market.state.base_vault(),
            ),
            AccountMeta(
                is_signer=False,
                is_writable=True,
                pubkey=pyserum_market.state.quote_vault(),
            ),
            AccountMeta(
                is_signer=False, is_writable=False, pubkey=base_root_bank.address
            ),
            AccountMeta(
                is_signer=False, is_writable=True, pubkey=base_node_bank.address
            ),
            AccountMeta(is_signer=False, is_writable=True, pubkey=base_node_bank.vault),
            AccountMeta(
                is_signer=False, is_writable=False, pubkey=quote_root_bank.address
            ),
            AccountMeta(
                is_signer=False, is_writable=True, pubkey=quote_node_bank.address
            ),
            AccountMeta(
                is_signer=False, is_writable=True, pubkey=quote_node_bank.vault
            ),
            AccountMeta(is_signer=False, is_writable=False, pubkey=TOKEN_PROGRAM_ID),
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.signer_key),
            AccountMeta(is_signer=False, is_writable=False, pubkey=vault_signer),
            AccountMeta(
                is_signer=False, is_writable=False, pubkey=fee_discount_address
            ),
            *list(
                [
                    AccountMeta(
                        is_signer=False,
                        is_writable=(oo_address == open_orders_address),
                        pubkey=oo_address,
                    )
                    for oo_address in account.spot_open_orders
                ]
            ),
        ],
        program_id=context.mango_program_address,
        data=layouts.PLACE_SPOT_ORDER_2.build(
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
        ),
    )

    return instructions + CombinableInstructions(
        signers=[], instructions=[place_spot_instruction]
    )


# # 🥭 build_spot_cancel_order_instructions function
#
# Builds the instructions necessary for cancelling a spot order.
#
def build_spot_cancel_order_instructions(
    context: Context,
    wallet: Wallet,
    group: IGroup,
    account: IAccount,
    market: PySerumMarket,
    order: Order,
    open_orders_address: PublicKey,
) -> CombinableInstructions:
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
                AccountMeta(
                    is_signer=False,
                    is_writable=False,
                    pubkey=context.serum_program_address,
                ),
                AccountMeta(
                    is_signer=False, is_writable=True, pubkey=market.state.public_key()
                ),
                AccountMeta(
                    is_signer=False, is_writable=True, pubkey=market.state.bids()
                ),
                AccountMeta(
                    is_signer=False, is_writable=True, pubkey=market.state.asks()
                ),
                AccountMeta(
                    is_signer=False, is_writable=True, pubkey=open_orders_address
                ),
                AccountMeta(
                    is_signer=False, is_writable=False, pubkey=group.signer_key
                ),
                AccountMeta(
                    is_signer=False, is_writable=True, pubkey=market.state.event_queue()
                ),
            ],
            program_id=context.mango_program_address,
            data=layouts.CANCEL_SPOT_ORDER.build(
                {"order_id": order.id, "side": raw_side}
            ),
        )
    ]
    return CombinableInstructions(signers=[], instructions=instructions)


# #
# # 🥭 Perp instruction builders
# #


# # 🥭 build_perp_cancel_order_instructions function
#
# Builds the instructions necessary for cancelling a perp order.
#
def build_perp_cancel_order_instructions(
    context: Context,
    wallet: Wallet,
    account: IAccount,
    perp_market_details: PerpMarketDetails,
    order: Order,
    invalid_id_ok: bool,
) -> CombinableInstructions:
    # Prefer cancelling by client ID so we don't have to keep track of the order side.
    if order.client_id is not None and order.client_id != 0:
        data: bytes = layouts.CANCEL_PERP_ORDER_BY_CLIENT_ID.build(
            {"client_order_id": order.client_id, "invalid_id_ok": invalid_id_ok}
        )
    else:
        data = layouts.CANCEL_PERP_ORDER.build(
            {"order_id": order.id, "invalid_id_ok": invalid_id_ok}
        )

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
                AccountMeta(
                    is_signer=False, is_writable=False, pubkey=account.group_address
                ),
                AccountMeta(is_signer=False, is_writable=True, pubkey=account.address),
                AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
                AccountMeta(
                    is_signer=False,
                    is_writable=True,
                    pubkey=perp_market_details.address,
                ),
                AccountMeta(
                    is_signer=False, is_writable=True, pubkey=perp_market_details.bids
                ),
                AccountMeta(
                    is_signer=False, is_writable=True, pubkey=perp_market_details.asks
                ),
            ],
            program_id=context.mango_program_address,
            data=data,
        )
    ]
    return CombinableInstructions(signers=[], instructions=instructions)


# # 🥭 build_perp_cancel_all_orders_instructions function
#
# Builds the instructions necessary for cancelling all perp orders.
#
def build_perp_cancel_all_orders_instructions(
    context: Context,
    wallet: Wallet,
    account: IAccount,
    perp_market_details: PerpMarketDetails,
    limit: Decimal = Decimal(32),
) -> CombinableInstructions:
    # Accounts expected by this instruction (seems to be the same as CANCEL_PERP_ORDER and CANCEL_PERP_ORDER_BY_CLIENT_ID):
    # { isSigner: false, isWritable: false, pubkey: mangoGroupPk },
    # { isSigner: false, isWritable: true, pubkey: mangoAccountPk },
    # { isSigner: true, isWritable: false, pubkey: ownerPk },
    # { isSigner: false, isWritable: true, pubkey: perpMarketPk },
    # { isSigner: false, isWritable: true, pubkey: bidsPk },
    # { isSigner: false, isWritable: true, pubkey: asksPk },
    instructions = [
        TransactionInstruction(
            keys=[
                AccountMeta(
                    is_signer=False, is_writable=False, pubkey=account.group_address
                ),
                AccountMeta(is_signer=False, is_writable=True, pubkey=account.address),
                AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
                AccountMeta(
                    is_signer=False,
                    is_writable=True,
                    pubkey=perp_market_details.address,
                ),
                AccountMeta(
                    is_signer=False, is_writable=True, pubkey=perp_market_details.bids
                ),
                AccountMeta(
                    is_signer=False, is_writable=True, pubkey=perp_market_details.asks
                ),
            ],
            program_id=context.mango_program_address,
            data=layouts.CANCEL_ALL_PERP_ORDERS.build({"limit": limit}),
        )
    ]
    return CombinableInstructions(signers=[], instructions=instructions)


# # 🥭 build_perp_cancel_all_side_instructions function
#
# Builds the instructions necessary for cancelling all perp orders on a given side.
#
def build_perp_cancel_all_side_instructions(
    context: Context,
    wallet: Wallet,
    account: IAccount,
    perp_market_details: PerpMarketDetails,
    side: Side,
    limit: Decimal = Decimal(32),
) -> CombinableInstructions:
    # { buy: 0, sell: 1 }
    raw_side: int = 1 if side == Side.SELL else 0

    # /// Cancel all perp open orders for one side of the book
    # ///
    # /// Accounts expected: 6
    # /// 0. `[]` mango_group_ai - MangoGroup
    # /// 1. `[writable]` mango_account_ai - MangoAccount
    # /// 2. `[signer]` owner_ai - Owner of Mango Account
    # /// 3. `[writable]` perp_market_ai - PerpMarket
    # /// 4. `[writable]` bids_ai - Bids acc
    # /// 5. `[writable]` asks_ai - Asks acc
    instructions = [
        TransactionInstruction(
            keys=[
                AccountMeta(
                    is_signer=False, is_writable=False, pubkey=account.group_address
                ),
                AccountMeta(is_signer=False, is_writable=True, pubkey=account.address),
                AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
                AccountMeta(
                    is_signer=False,
                    is_writable=True,
                    pubkey=perp_market_details.address,
                ),
                AccountMeta(
                    is_signer=False, is_writable=True, pubkey=perp_market_details.bids
                ),
                AccountMeta(
                    is_signer=False, is_writable=True, pubkey=perp_market_details.asks
                ),
            ],
            program_id=context.mango_program_address,
            data=layouts.CANCEL_PERP_ORDER_SIDE.build(
                {"side": raw_side, "limit": limit}
            ),
        )
    ]
    return CombinableInstructions(signers=[], instructions=instructions)


# /// Place an order on a perp market
# ///
# /// In case this order is matched, the corresponding order structs on both
# /// PerpAccounts (taker & maker) will be adjusted, and the position size
# /// will be adjusted w/o accounting for fees.
# /// In addition a FillEvent will be placed on the event queue.
# /// Through a subsequent invocation of ConsumeEvents the FillEvent can be
# /// executed and the perp account balances (base/quote) and fees will be
# /// paid from the quote position. Only at this point the position balance
# /// is 100% reflecting the trade.
# ///
# /// Accounts expected by this instruction (9 + `NUM_IN_MARGIN_BASKET`):
# /// 0. `[]` mango_group_ai - MangoGroup
# /// 1. `[writable]` mango_account_ai - the MangoAccount of owner
# /// 2. `[signer]` owner_ai - owner of MangoAccount
# /// 3. `[]` mango_cache_ai - MangoCache for this MangoGroup
# /// 4. `[writable]` perp_market_ai
# /// 5. `[writable]` bids_ai - bids account for this PerpMarket
# /// 6. `[writable]` asks_ai - asks account for this PerpMarket
# /// 7. `[writable]` event_queue_ai - EventQueue for this PerpMarket
# /// 8. `[writable]` referrer_mango_account_ai - referrer's mango account;
# ///                 pass in mango_account_ai as duplicate if you don't have a referrer
# /// 9..9 + NUM_IN_MARGIN_BASKET `[]` open_orders_ais - pass in open orders in margin basket
def build_perp_place_order_instructions(
    context: Context,
    wallet: Wallet,
    group: IGroup,
    account: IAccount,
    perp_market_details: PerpMarketDetails,
    price: Decimal,
    quantity: Decimal,
    client_order_id: int,
    side: Side,
    order_type: OrderType,
    reduce_only: bool = False,
    expiration: datetime = Order.NoExpiration,
    match_limit: int = 20,
    max_quote_quantity: Decimal = Decimal(0),
    reflink: typing.Optional[PublicKey] = None,
) -> CombinableInstructions:
    # { buy: 0, sell: 1 }
    raw_side: int = 1 if side == Side.SELL else 0
    raw_order_type: int = order_type.to_perp()

    base_decimals = perp_market_details.base_instrument.decimals
    quote_decimals = perp_market_details.quote_token.token.decimals

    base_factor = Decimal(10) ** base_decimals
    quote_factor = Decimal(10) ** quote_decimals

    native_price = ((price * quote_factor) * perp_market_details.base_lot_size) / (
        perp_market_details.quote_lot_size * base_factor
    )
    native_quantity = (quantity * base_factor) / perp_market_details.base_lot_size
    native_max_quote_quantity = (
        (max_quote_quantity * quote_factor) / perp_market_details.quote_lot_size
    ) or I64_MAX

    # /// Accounts expected by this instruction (9 + `NUM_IN_MARGIN_BASKET`):
    # /// 0. `[]` mango_group_ai - MangoGroup
    # /// 1. `[writable]` mango_account_ai - the MangoAccount of owner
    # /// 2. `[signer]` owner_ai - owner of MangoAccount
    # /// 3. `[]` mango_cache_ai - MangoCache for this MangoGroup
    # /// 4. `[writable]` perp_market_ai
    # /// 5. `[writable]` bids_ai - bids account for this PerpMarket
    # /// 6. `[writable]` asks_ai - asks account for this PerpMarket
    # /// 7. `[writable]` event_queue_ai - EventQueue for this PerpMarket
    # /// 8. `[writable]` referrer_mango_account_ai - referrer's mango account;
    # ///                 pass in mango_account_ai as duplicate if you don't have a referrer
    # /// 9..9 + NUM_IN_MARGIN_BASKET `[]` open_orders_ais - pass in open orders in margin basket
    keys = [
        AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
        AccountMeta(is_signer=False, is_writable=True, pubkey=account.address),
        AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
        AccountMeta(is_signer=False, is_writable=False, pubkey=group.cache),
        AccountMeta(
            is_signer=False, is_writable=True, pubkey=perp_market_details.address
        ),
        AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market_details.bids),
        AccountMeta(is_signer=False, is_writable=True, pubkey=perp_market_details.asks),
        AccountMeta(
            is_signer=False, is_writable=True, pubkey=perp_market_details.event_queue
        ),
        AccountMeta(
            is_signer=False, is_writable=True, pubkey=reflink or account.address
        ),
        *list(
            [
                AccountMeta(
                    is_signer=False,
                    is_writable=False,
                    pubkey=oo_address,
                )
                for oo_address in account.spot_open_orders
            ]
        ),
    ]

    instructions = [
        TransactionInstruction(
            keys=keys,
            program_id=context.mango_program_address,
            data=layouts.PLACE_PERP_ORDER_2.build(
                {
                    "price": native_price,
                    "max_base_quantity": native_quantity,
                    "max_quote_quantity": native_max_quote_quantity,
                    "client_order_id": client_order_id,
                    "expiry_timestamp": expiration,
                    "side": raw_side,
                    "order_type": raw_order_type,
                    "reduce_only": reduce_only,
                    "limit": match_limit,
                }
            ),
        )
    ]

    return CombinableInstructions(signers=[], instructions=instructions)


def build_perp_consume_events_instructions(
    context: Context,
    group: IGroup,
    perp_market_details: PerpMarketDetails,
    account_addresses: typing.Sequence[PublicKey],
    limit: Decimal = Decimal(32),
) -> CombinableInstructions:
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
                AccountMeta(
                    is_signer=False,
                    is_writable=True,
                    pubkey=perp_market_details.address,
                ),
                AccountMeta(
                    is_signer=False,
                    is_writable=True,
                    pubkey=perp_market_details.event_queue,
                ),
                *list(
                    [
                        AccountMeta(
                            is_signer=False, is_writable=True, pubkey=account_address
                        )
                        for account_address in account_addresses
                    ]
                ),
            ],
            program_id=context.mango_program_address,
            data=layouts.CONSUME_EVENTS.build(
                {
                    "limit": limit,
                }
            ),
        )
    ]
    return CombinableInstructions(signers=[], instructions=instructions)


# #
# # 🥭 Mango instruction builders
# #


# The old INIT_MANGO_ACCOUNT instruction is now superseded by CREATE_MANGO_ACCOUNT
def build_mango_create_account_instructions(
    context: Context, wallet: Wallet, group: IGroup, account_num: Decimal = Decimal(1)
) -> CombinableInstructions:
    mango_account_address_and_nonce: typing.Tuple[
        PublicKey, int
    ] = PublicKey.find_program_address(
        [
            bytes(group.address),
            bytes(wallet.address),
            int(account_num).to_bytes(8, "little"),
        ],
        context.mango_program_address,
    )
    mango_account_address: PublicKey = mango_account_address_and_nonce[0]

    # /// 0. `[writable]` mango_group_ai - MangoGroup that this mango account is for
    # /// 1. `[writable]` mango_account_ai - the mango account data
    # /// 2. `[signer]` owner_ai - Solana account of owner of the mango account
    # /// 3. `[]` system_prog_ai - System program
    create = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=True, pubkey=group.address),
            AccountMeta(
                is_signer=False, is_writable=True, pubkey=mango_account_address
            ),
            AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
            AccountMeta(
                is_signer=False, is_writable=False, pubkey=SYSTEM_PROGRAM_ADDRESS
            ),
        ],
        program_id=context.mango_program_address,
        data=layouts.CREATE_MANGO_ACCOUNT.build({"account_num": account_num}),
    )
    return CombinableInstructions(signers=[], instructions=[create])


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
def build_mango_deposit_instructions(
    context: Context,
    wallet: Wallet,
    group: IGroup,
    account: IAccount,
    root_bank: RootBank,
    node_bank: NodeBank,
    token_account: TokenAccount,
) -> CombinableInstructions:
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
            AccountMeta(
                is_signer=False, is_writable=True, pubkey=token_account.address
            ),
        ],
        program_id=context.mango_program_address,
        data=layouts.DEPOSIT.build({"quantity": value}),
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
def build_mango_withdraw_instructions(
    context: Context,
    wallet: Wallet,
    group: IGroup,
    account: IAccount,
    root_bank: RootBank,
    node_bank: NodeBank,
    token_account: TokenAccount,
    allow_borrow: bool,
) -> CombinableInstructions:
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
            AccountMeta(
                is_signer=False, is_writable=True, pubkey=token_account.address
            ),
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.signer_key),
            AccountMeta(is_signer=False, is_writable=False, pubkey=TOKEN_PROGRAM_ID),
            *list(
                [
                    AccountMeta(
                        is_signer=False,
                        is_writable=False,
                        pubkey=oo_address or SYSTEM_PROGRAM_ADDRESS,
                    )
                    for oo_address in account.spot_open_orders_by_index
                ]
            ),
        ],
        program_id=context.mango_program_address,
        data=layouts.WITHDRAW.build({"quantity": value, "allow_borrow": allow_borrow}),
    )

    return CombinableInstructions(signers=[], instructions=[withdraw])


# # 🥭 build_mango_redeem_accrued_instructions function
#
# Creates a 'RedeemMngo' instruction for Mango accounts.
#
def build_mango_redeem_accrued_instructions(
    context: Context,
    wallet: Wallet,
    perp_market: IPerpMarket,
    group: IGroup,
    account: IAccount,
    mngo: TokenBank,
) -> CombinableInstructions:
    node_bank: NodeBank = mngo.pick_node_bank(context)
    # /// Redeem the mngo_accrued in a PerpAccount for MNGO in MangoAccount deposits
    # ///
    # /// Accounts expected by this instruction (11):
    # /// 0. `[]` mango_group_ai - MangoGroup that this mango account is for
    # /// 1. `[]` mango_cache_ai - MangoCache
    # /// 2. `[writable]` mango_account_ai - MangoAccount
    # /// 3. `[signer]` owner_ai - MangoAccount owner
    # /// 4. `[]` perp_market_ai - IPerpMarket
    # /// 5. `[writable]` mngo_perp_vault_ai
    # /// 6. `[]` mngo_root_bank_ai
    # /// 7. `[writable]` mngo_node_bank_ai
    # /// 8. `[writable]` mngo_bank_vault_ai
    # /// 9. `[]` signer_ai - IGroup Signer IAccount
    # /// 10. `[]` token_prog_ai - SPL Token program id
    redeem_accrued_mango_instruction = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.cache),
            AccountMeta(is_signer=False, is_writable=True, pubkey=account.address),
            AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=perp_market.address),
            AccountMeta(
                is_signer=False,
                is_writable=True,
                pubkey=perp_market.underlying_perp_market.mngo_vault,
            ),
            AccountMeta(
                is_signer=False, is_writable=False, pubkey=mngo.root_bank_address
            ),
            AccountMeta(is_signer=False, is_writable=True, pubkey=node_bank.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=node_bank.vault),
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.signer_key),
            AccountMeta(is_signer=False, is_writable=False, pubkey=TOKEN_PROGRAM_ID),
        ],
        program_id=context.mango_program_address,
        data=layouts.REDEEM_MNGO.build({}),
    )
    return CombinableInstructions(
        signers=[], instructions=[redeem_accrued_mango_instruction]
    )


# # 🥭 build_mango_set_account_delegate_instructions function
#
# Creates an instruction to delegate account operations (except Withdraw and CloseAccount) to a
# different account.
#
# Set to SYSTEM_PROGRAM_ADDRESS to revoke delegate.
#
def build_mango_set_account_delegate_instructions(
    context: Context,
    wallet: Wallet,
    group: IGroup,
    account: IAccount,
    delegate: PublicKey,
) -> CombinableInstructions:
    # /// https://github.com/blockworks-foundation/mango-v3/pull/97/
    # /// Set delegate authority to mango account which can do everything regular account can do
    # /// except Withdraw and CloseMangoAccount. Set to Pubkey::default() to revoke delegate
    # ///
    # /// Accounts expected: 4
    # /// 0. `[]` mango_group_ai - MangoGroup
    # /// 1. `[writable]` mango_account_ai - MangoAccount
    # /// 2. `[signer]` owner_ai - Owner of Mango IAccount
    # /// 3. `[]` delegate_ai - delegate
    set_delegate_instruction = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=account.address),
            AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=delegate),
        ],
        program_id=context.mango_program_address,
        data=layouts.SET_DELEGATE.build({}),
    )
    return CombinableInstructions(signers=[], instructions=[set_delegate_instruction])


def build_mango_unset_account_delegate_instructions(
    context: Context, wallet: Wallet, group: IGroup, account: IAccount
) -> CombinableInstructions:
    return build_mango_set_account_delegate_instructions(
        context, wallet, group, account, SYSTEM_PROGRAM_ADDRESS
    )


# # 🥭 build_mango_set_referrer_memory_instructions function
#
# Creates an instruction to store the referrer's MangoAccount pubkey on the Referrer account
# and create the Referrer account as a PDA of user's MangoAccount if it doesn't exist
#
def build_mango_set_referrer_memory_instructions(
    context: Context,
    wallet: Wallet,
    group: IGroup,
    account: IAccount,
    referrer_memory_address: PublicKey,
    referrer_account_address: PublicKey,
) -> CombinableInstructions:
    # /// Store the referrer's MangoAccount pubkey on the Referrer account
    # /// It will create the Referrer account as a PDA of user's MangoAccount if it doesn't exist
    # /// This is primarily useful for the UI; the referrer address stored here is not necessarily
    # /// who earns the ref fees.
    # ///
    # /// Accounts expected by this instruction (7):
    # ///
    # /// 0. `[]` mango_group_ai - MangoGroup that this mango account is for
    # /// 1. `[]` mango_account_ai - MangoAccount of the referred
    # /// 2. `[signer]` owner_ai - MangoAccount owner or delegate
    # /// 3. `[writable]` referrer_memory_ai - ReferrerMemory struct; will be initialized if required
    # /// 4. `[]` referrer_mango_account_ai - referrer's MangoAccount
    # /// 5. `[signer, writable]` payer_ai - payer for PDA; can be same as owner
    # /// 6. `[]` system_prog_ai - System program
    set_referrer_memory_instruction = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=account.address),
            AccountMeta(is_signer=True, is_writable=False, pubkey=wallet.address),
            AccountMeta(
                is_signer=False, is_writable=True, pubkey=referrer_memory_address
            ),
            AccountMeta(
                is_signer=False, is_writable=True, pubkey=referrer_account_address
            ),
            AccountMeta(is_signer=True, is_writable=True, pubkey=wallet.address),
            AccountMeta(
                is_signer=False, is_writable=False, pubkey=SYSTEM_PROGRAM_ADDRESS
            ),
        ],
        program_id=context.mango_program_address,
        data=layouts.SET_REFERRER_MEMORY.build({}),
    )
    return CombinableInstructions(
        signers=[], instructions=[set_referrer_memory_instruction]
    )


# # 🥭 build_mango_register_referrer_id_instructions function
#
# Creates an instruction to register a 'referrer ID' for a Mango IAccount
#
def build_mango_register_referrer_id_instructions(
    context: Context,
    wallet: Wallet,
    group: IGroup,
    account: IAccount,
    referrer_record_address: PublicKey,
    referrer_id: str,
) -> CombinableInstructions:
    # /// Associate the referrer's MangoAccount with a human readable `referrer_id` which can be used
    # /// in a ref link. This is primarily useful for the UI.
    # /// Create the `ReferrerIdRecord` PDA; if it already exists throw error
    # ///
    # /// Accounts expected by this instruction (5):
    # /// 0. `[]` mango_group_ai - MangoGroup
    # /// 1. `[]` referrer_mango_account_ai - MangoAccount
    # /// 2. `[writable]` referrer_id_record_ai - The PDA to store the record on
    # /// 3. `[signer, writable]` payer_ai - payer for PDA; can be same as owner
    # /// 4. `[]` system_prog_ai - System program
    register_referrer_id_instruction = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=account.address),
            AccountMeta(
                is_signer=False, is_writable=True, pubkey=referrer_record_address
            ),
            AccountMeta(is_signer=True, is_writable=True, pubkey=wallet.address),
            AccountMeta(
                is_signer=False, is_writable=False, pubkey=SYSTEM_PROGRAM_ADDRESS
            ),
        ],
        program_id=context.mango_program_address,
        data=layouts.REGISTER_REFERRER_ID.build({"info": referrer_id}),
    )
    return CombinableInstructions(
        signers=[], instructions=[register_referrer_id_instruction]
    )


def build_mango_cache_root_banks_instructions(
    context: Context,
    group: IGroup,
    root_banks: typing.Sequence[PublicKey],
) -> CombinableInstructions:
    # /// DEPRECATED - caching of root banks now happens in update index
    # /// Cache root banks
    # ///
    # /// Accounts expected: 2 + Root Banks
    # /// 0. `[]` mango_group_ai
    # /// 1. `[writable]` mango_cache_ai
    instruction = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=group.cache),
            *list(
                [
                    AccountMeta(
                        is_signer=False,
                        is_writable=False,
                        pubkey=root_bank,
                    )
                    for root_bank in root_banks
                ]
            ),
        ],
        program_id=context.mango_program_address,
        data=layouts.CACHE_ROOT_BANKS.build({}),
    )
    return CombinableInstructions(signers=[], instructions=[instruction])


def build_mango_cache_prices_instructions(
    context: Context,
    group: IGroup,
    oracle_addresses: typing.Sequence[PublicKey],
) -> CombinableInstructions:
    # /// Cache prices
    # ///
    # /// Accounts expected: 3 + Oracles
    # /// 0. `[]` mango_group_ai -
    # /// 1. `[writable]` mango_cache_ai -
    # /// 2+... `[]` oracle_ais - flux aggregator feed accounts
    instruction = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=group.cache),
            *list(
                [
                    AccountMeta(
                        is_signer=False,
                        is_writable=False,
                        pubkey=oracle,
                    )
                    for oracle in oracle_addresses
                ]
            ),
        ],
        program_id=context.mango_program_address,
        data=layouts.CACHE_PRICES.build({}),
    )
    return CombinableInstructions(signers=[], instructions=[instruction])


def build_mango_cache_perp_markets_instructions(
    context: Context,
    group: IGroup,
    perp_market_addresses: typing.Sequence[PublicKey],
) -> CombinableInstructions:
    # /// Cache perp markets
    # ///
    # /// Accounts expected: 2 + Perp Markets
    # /// 0. `[]` mango_group_ai
    # /// 1. `[writable]` mango_cache_ai
    instruction = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=group.cache),
            *map(
                lambda address: AccountMeta(
                    is_signer=False,
                    is_writable=False,
                    pubkey=address,
                ),
                perp_market_addresses,
            ),
        ],
        program_id=context.mango_program_address,
        data=layouts.CACHE_PERP_MARKETS.build({}),
    )
    return CombinableInstructions(signers=[], instructions=[instruction])


def build_mango_update_root_bank_instructions(
    context: Context,
    group: IGroup,
    root_bank: PublicKey,
    node_banks: typing.Sequence[PublicKey],
) -> CombinableInstructions:
    # /// Update a root bank's indexes by providing all it's node banks
    # ///
    # /// Accounts expected: 2 + Node Banks
    # /// 0. `[]` mango_group_ai - MangoGroup
    # /// 1. `[]` root_bank_ai - RootBank
    # /// 2+... `[]` node_bank_ais - NodeBanks
    #
    # Note: The above doesn't seem quite right. It seems to need the Cache as [1], and
    # cache+banks all seem to need to be writable.
    instruction = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=group.cache),
            AccountMeta(is_signer=False, is_writable=True, pubkey=root_bank),
            *list(
                [
                    AccountMeta(
                        is_signer=False,
                        is_writable=True,
                        pubkey=node_bank,
                    )
                    for node_bank in node_banks
                ]
            ),
        ],
        program_id=context.mango_program_address,
        data=layouts.UPDATE_ROOT_BANK.build({}),
    )
    return CombinableInstructions(signers=[], instructions=[instruction])


def build_mango_update_funding_instructions(
    context: Context,
    group: IGroup,
    perp_market_details: PerpMarketDetails,
) -> CombinableInstructions:
    # /// Update funding related variables
    #
    # Seems to take:
    #   const keys = [
    #     { isSigner: false, isWritable: false, pubkey: mangoGroupPk },
    #     { isSigner: false, isWritable: true, pubkey: mangoCachePk },
    #     { isSigner: false, isWritable: true, pubkey: perpMarketPk },
    #     { isSigner: false, isWritable: false, pubkey: bidsPk },
    #     { isSigner: false, isWritable: false, pubkey: asksPk },
    #   ];
    instruction = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=group.cache),
            AccountMeta(
                is_signer=False, is_writable=True, pubkey=perp_market_details.address
            ),
            AccountMeta(
                is_signer=False, is_writable=False, pubkey=perp_market_details.bids
            ),
            AccountMeta(
                is_signer=False, is_writable=False, pubkey=perp_market_details.asks
            ),
        ],
        program_id=context.mango_program_address,
        data=layouts.UPDATE_FUNDING.build({}),
    )
    return CombinableInstructions(signers=[], instructions=[instruction])


def build_mango_settle_fees_instructions(
    context: Context,
    group: IGroup,
    perp_market_details: PerpMarketDetails,
    account: IAccount,
    root_bank: RootBank,
    node_bank: NodeBank,
) -> CombinableInstructions:
    # /// Take an account that has losses in the selected perp market to account for fees_accrued
    # ///
    # /// Accounts expected: 10
    # /// 0. `[]` mango_group_ai - MangoGroup
    # /// 1. `[]` mango_cache_ai - MangoCache
    # /// 2. `[writable]` perp_market_ai - PerpMarket
    # /// 3. `[writable]` mango_account_ai - MangoAccount
    # /// 4. `[]` root_bank_ai - RootBank
    # /// 5. `[writable]` node_bank_ai - NodeBank
    # /// 6. `[writable]` bank_vault_ai - ?
    # /// 7. `[writable]` fees_vault_ai - fee vault owned by mango DAO token governance
    # /// 8. `[]` signer_ai - Group Signer Account
    # /// 9. `[]` token_prog_ai - Token Program Account
    instruction = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.cache),
            AccountMeta(
                is_signer=False, is_writable=True, pubkey=perp_market_details.address
            ),
            AccountMeta(is_signer=False, is_writable=True, pubkey=account.address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=root_bank.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=node_bank.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=node_bank.vault),
            AccountMeta(is_signer=False, is_writable=True, pubkey=group.fees_vault),
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.signer_key),
            AccountMeta(is_signer=False, is_writable=False, pubkey=TOKEN_PROGRAM_ID),
        ],
        program_id=context.mango_program_address,
        data=layouts.SETTLE_FEES.build({}),
    )
    return CombinableInstructions(signers=[], instructions=[instruction])


def build_mango_settle_pnl_instructions(
    context: Context,
    group: IGroup,
    group_slot: IGroupSlot,
    account_a: IAccount,
    account_b: IAccount,
    root_bank: RootBank,
) -> CombinableInstructions:
    # /// Take two MangoAccounts and settle profits and losses between them for a perp market
    # ///
    # /// Accounts expected (6):
    #   const keys = [
    #     { isSigner: false, isWritable: false, pubkey: mangoGroupPk },
    #     { isSigner: false, isWritable: true, pubkey: mangoAccountAPk },
    #     { isSigner: false, isWritable: true, pubkey: mangoAccountBPk },
    #     { isSigner: false, isWritable: false, pubkey: mangoCachePk },
    #     { isSigner: false, isWritable: false, pubkey: rootBankPk },
    #     { isSigner: false, isWritable: true, pubkey: nodeBankPk },
    #   ];
    instruction = TransactionInstruction(
        keys=[
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=account_a.address),
            AccountMeta(is_signer=False, is_writable=True, pubkey=account_b.address),
            AccountMeta(is_signer=False, is_writable=False, pubkey=group.cache),
            AccountMeta(is_signer=False, is_writable=False, pubkey=root_bank.address),
            AccountMeta(
                is_signer=False, is_writable=True, pubkey=root_bank.node_banks[0]
            ),
        ],
        program_id=context.mango_program_address,
        data=layouts.SETTLE_PNL.build({"market_index": group_slot.index}),
    )
    return CombinableInstructions(signers=[], instructions=[instruction])
