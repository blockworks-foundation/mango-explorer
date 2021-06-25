# # ⚠ Warning
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
# NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# [🥭 Mango Markets](https://markets/) support is available at:
#   [Docs](https://docs.markets/)
#   [Discord](https://discord.gg/67jySBhxrg)
#   [Twitter](https://twitter.com/mangomarkets)
#   [Github](https://github.com/blockworks-foundation)
#   [Email](mailto:hello@blockworks.foundation)

import typing

from decimal import Decimal
from solana.account import Account
from solana.system_program import CreateAccountParams, create_account
from solana.sysvar import SYSVAR_CLOCK_PUBKEY
from solana.transaction import AccountMeta, TransactionInstruction
from spl.token.constants import TOKEN_PROGRAM_ID

from .constants import SYSTEM_PROGRAM_ADDRESS
from .context import Context
from .layouts import layouts
from .mangoaccount import MangoAccount
from .mangogroup import MangoGroup
from .orders import Order, OrderType, Side
from .perpmarket import PerpMarket
from .rootbank import NodeBank, RootBank
from .tokenaccount import TokenAccount
from .wallet import Wallet

# # 🥭 build_cancel_perp_order_instruction function
#
# Builds the instructions necessary for cancelling a perp order.
#


def build_cancel_perp_order_instructions(context: Context, wallet: Wallet, margin_account: MangoAccount, perp_market: PerpMarket, order: Order) -> typing.Sequence[TransactionInstruction]:
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


def build_place_perp_order_instructions(context: Context, wallet: Wallet, group: MangoGroup, margin_account: MangoAccount, perp_market: PerpMarket, price: Decimal, quantity: Decimal, client_order_id: int, side: Side, order_type: OrderType) -> typing.Sequence[TransactionInstruction]:
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


def build_create_margin_account_instructions(context: Context, wallet: Wallet, group: MangoGroup, new_account: Account) -> typing.Sequence[TransactionInstruction]:
    mango_account_address = new_account.public_key()

    minimum_balance_response = context.client.get_minimum_balance_for_rent_exemption(layouts.MANGO_ACCOUNT.sizeof())
    minimum_balance = context.unwrap_or_raise_exception(minimum_balance_response)
    create = create_account(
        CreateAccountParams(wallet.address, mango_account_address, minimum_balance, layouts.MANGO_ACCOUNT.sizeof(), context.program_id))
    # /// 0. `[]` mango_group_ai - MangoGroup that this mango account is for
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
def build_withdraw_instructions(context: Context, wallet: Wallet, group: MangoGroup, margin_account: MangoAccount, root_bank: RootBank, node_bank: NodeBank, token_account: TokenAccount, allow_borrow: bool) -> typing.Sequence[TransactionInstruction]:
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
