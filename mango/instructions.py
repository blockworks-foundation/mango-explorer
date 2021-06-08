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
import struct
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
from solana.sysvar import SYSVAR_CLOCK_PUBKEY
from spl.token.constants import ACCOUNT_LEN, TOKEN_PROGRAM_ID
from spl.token.instructions import CloseAccountParams, InitializeAccountParams, Transfer2Params, close_account, initialize_account, transfer2

from .baskettoken import BasketToken
from .context import Context
from .group import Group
from .layouts import layouts
from .marginaccount import MarginAccount
from .marketmetadata import MarketMetadata
from .token import Token
from .tokenaccount import TokenAccount
from .tokenvalue import TokenValue
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


# # 🥭 ForceCancelOrdersInstructionBuilder class
#
#
# ## Rust Interface
#
# This is what the `force_cancel_orders` instruction looks like in the [Mango Rust](https://github.com/blockworks-foundation/mango/blob/master/program/src/instruction.rs) code:
# ```
# pub fn force_cancel_orders(
#     program_id: &Pubkey,
#     mango_group_pk: &Pubkey,
#     liqor_pk: &Pubkey,
#     liqee_margin_account_acc: &Pubkey,
#     base_vault_pk: &Pubkey,
#     quote_vault_pk: &Pubkey,
#     spot_market_pk: &Pubkey,
#     bids_pk: &Pubkey,
#     asks_pk: &Pubkey,
#     signer_pk: &Pubkey,
#     dex_event_queue_pk: &Pubkey,
#     dex_base_pk: &Pubkey,
#     dex_quote_pk: &Pubkey,
#     dex_signer_pk: &Pubkey,
#     dex_prog_id: &Pubkey,
#     open_orders_pks: &[Pubkey],
#     oracle_pks: &[Pubkey],
#     limit: u8
# ) -> Result<Instruction, ProgramError>
# ```
#
# ## Client API call
#
# This is how it is built using the Mango Markets client API:
# ```
#   const keys = [
#     { isSigner: false, isWritable: true, pubkey: mangoGroup },
#     { isSigner: true, isWritable: false, pubkey: liqor },
#     { isSigner: false, isWritable: true, pubkey: liqeeMarginAccount },
#     { isSigner: false, isWritable: true, pubkey: baseVault },
#     { isSigner: false, isWritable: true, pubkey: quoteVault },
#     { isSigner: false, isWritable: true, pubkey: spotMarket },
#     { isSigner: false, isWritable: true, pubkey: bids },
#     { isSigner: false, isWritable: true, pubkey: asks },
#     { isSigner: false, isWritable: false, pubkey: signerKey },
#     { isSigner: false, isWritable: true, pubkey: dexEventQueue },
#     { isSigner: false, isWritable: true, pubkey: dexBaseVault },
#     { isSigner: false, isWritable: true, pubkey: dexQuoteVault },
#     { isSigner: false, isWritable: false, pubkey: dexSigner },
#     { isSigner: false, isWritable: false, pubkey: TOKEN_PROGRAM_ID },
#     { isSigner: false, isWritable: false, pubkey: dexProgramId },
#     { isSigner: false, isWritable: false, pubkey: SYSVAR_CLOCK_PUBKEY },
#     ...openOrders.map((pubkey) => ({
#       isSigner: false,
#       isWritable: true,
#       pubkey,
#     })),
#     ...oracles.map((pubkey) => ({
#       isSigner: false,
#       isWritable: false,
#       pubkey,
#     })),
#   ];
#
#   const data = encodeMangoInstruction({ ForceCancelOrders: { limit } });
#   return new TransactionInstruction({ keys, data, programId });
# ```
#

class ForceCancelOrdersInstructionBuilder(InstructionBuilder):
    # We can create up to a maximum of max_instructions instructions. I'm not sure of the reason
    # for this threshold but it's what's in the original liquidator source code and I'm assuming
    # it's there for a good reason.
    max_instructions: int = 10

    # We cancel up to max_cancels_per_instruction orders with each instruction.
    max_cancels_per_instruction: int = 5

    def __init__(self, context: Context, group: Group, wallet: Wallet, margin_account: MarginAccount, market_metadata: MarketMetadata, market: Market, oracles: typing.List[PublicKey], dex_signer: PublicKey):
        super().__init__(context)
        self.group = group
        self.wallet = wallet
        self.margin_account = margin_account
        self.market_metadata = market_metadata
        self.market = market
        self.oracles = oracles
        self.dex_signer = dex_signer

    def build(self) -> TransactionInstruction:
        transaction = TransactionInstruction(
            keys=[
                AccountMeta(is_signer=False, is_writable=True, pubkey=self.group.address),
                AccountMeta(is_signer=True, is_writable=False, pubkey=self.wallet.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=self.margin_account.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=self.market_metadata.base.vault),
                AccountMeta(is_signer=False, is_writable=True, pubkey=self.market_metadata.quote.vault),
                AccountMeta(is_signer=False, is_writable=True, pubkey=self.market_metadata.spot.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=self.market.state.bids()),
                AccountMeta(is_signer=False, is_writable=True, pubkey=self.market.state.asks()),
                AccountMeta(is_signer=False, is_writable=False, pubkey=self.group.signer_key),
                AccountMeta(is_signer=False, is_writable=True, pubkey=self.market.state.event_queue()),
                AccountMeta(is_signer=False, is_writable=True, pubkey=self.market.state.base_vault()),
                AccountMeta(is_signer=False, is_writable=True, pubkey=self.market.state.quote_vault()),
                AccountMeta(is_signer=False, is_writable=False, pubkey=self.dex_signer),
                AccountMeta(is_signer=False, is_writable=False, pubkey=TOKEN_PROGRAM_ID),
                AccountMeta(is_signer=False, is_writable=False, pubkey=self.context.dex_program_id),
                AccountMeta(is_signer=False, is_writable=False, pubkey=SYSVAR_CLOCK_PUBKEY),
                *list([AccountMeta(is_signer=False, is_writable=True, pubkey=oo_address)
                      for oo_address in self.margin_account.open_orders]),
                *list([AccountMeta(is_signer=False, is_writable=False, pubkey=oracle_address) for oracle_address in self.oracles])
            ],
            program_id=self.context.program_id,
            data=layouts.FORCE_CANCEL_ORDERS.build(
                {"limit": ForceCancelOrdersInstructionBuilder.max_cancels_per_instruction})
        )
        self.logger.debug(f"Built transaction: {transaction}")
        return transaction

    @staticmethod
    def from_margin_account_and_market(context: Context, group: Group, wallet: Wallet, margin_account: MarginAccount, market_metadata: MarketMetadata) -> "ForceCancelOrdersInstructionBuilder":
        market = market_metadata.fetch_market(context)
        nonce = struct.pack("<Q", market.state.vault_signer_nonce())
        dex_signer = PublicKey.create_program_address(
            [bytes(market_metadata.spot.address), nonce], context.dex_program_id)
        oracles = list([mkt.oracle for mkt in group.markets])

        return ForceCancelOrdersInstructionBuilder(context, group, wallet, margin_account, market_metadata, market, oracles, dex_signer)

    @classmethod
    def multiple_instructions_from_margin_account_and_market(cls, context: Context, group: Group, wallet: Wallet, margin_account: MarginAccount, market_metadata: MarketMetadata, at_least_this_many_cancellations: int) -> typing.List["ForceCancelOrdersInstructionBuilder"]:
        logger: logging.Logger = logging.getLogger(cls.__name__)

        # We cancel up to max_cancels_per_instruction orders with each instruction, but if
        # we have more than cancel_limit we create more instructions (each handling up to
        # 5 orders)
        calculated_instruction_count = int(
            at_least_this_many_cancellations / ForceCancelOrdersInstructionBuilder.max_cancels_per_instruction) + 1

        # We create a maximum of max_instructions instructions.
        instruction_count = min(calculated_instruction_count, ForceCancelOrdersInstructionBuilder.max_instructions)

        instructions: typing.List[ForceCancelOrdersInstructionBuilder] = []
        for counter in range(instruction_count):
            instructions += [ForceCancelOrdersInstructionBuilder.from_margin_account_and_market(
                context, group, wallet, margin_account, market_metadata)]

        logger.debug(f"Built {len(instructions)} transaction(s).")

        return instructions

    def __str__(self) -> str:
        # Print the members out using the Rust parameter order and names.
        return f"""« ForceCancelOrdersInstructionBuilder:
    program_id: &Pubkey: {self.context.program_id},
    mango_group_pk: &Pubkey: {self.group.address},
    liqor_pk: &Pubkey: {self.wallet.address},
    liqee_margin_account_acc: &Pubkey: {self.margin_account.address},
    base_vault_pk: &Pubkey: {self.market_metadata.base.vault},
    quote_vault_pk: &Pubkey: {self.market_metadata.quote.vault},
    spot_market_pk: &Pubkey: {self.market_metadata.spot.address},
    bids_pk: &Pubkey: {self.market.state.bids()},
    asks_pk: &Pubkey: {self.market.state.asks()},
    signer_pk: &Pubkey: {self.group.signer_key},
    dex_event_queue_pk: &Pubkey: {self.market.state.event_queue()},
    dex_base_pk: &Pubkey: {self.market.state.base_vault()},
    dex_quote_pk: &Pubkey: {self.market.state.quote_vault()},
    dex_signer_pk: &Pubkey: {self.dex_signer},
    dex_prog_id: &Pubkey: {self.context.dex_program_id},
    open_orders_pks: &[Pubkey]: {self.margin_account.open_orders},
    oracle_pks: &[Pubkey]: {self.oracles},
    limit: u8: {ForceCancelOrdersInstructionBuilder.max_cancels_per_instruction}
»"""


# # 🥭 LiquidateInstructionBuilder class
#
# This is the `Instruction` we send to Solana to perform the (partial) liquidation.
#
# We take care to pass the proper high-level parameters to the `LiquidateInstructionBuilder`
# constructor so that `build_transaction()` is straightforward. That tends to push
# complexities to `from_margin_account_and_market()` though.
#
# ## Rust Interface
#
# This is what the `partial_liquidate` instruction looks like in the [Mango Rust](https://github.com/blockworks-foundation/mango/blob/master/program/src/instruction.rs) code:
# ```
# /// Take over a MarginAccount that is below init_coll_ratio by depositing funds
# ///
# /// Accounts expected by this instruction (10 + 2 * NUM_MARKETS):
# ///
# /// 0. `[writable]` mango_group_acc - MangoGroup that this margin account is for
# /// 1. `[signer]` liqor_acc - liquidator's solana account
# /// 2. `[writable]` liqor_in_token_acc - liquidator's token account to deposit
# /// 3. `[writable]` liqor_out_token_acc - liquidator's token account to withdraw into
# /// 4. `[writable]` liqee_margin_account_acc - MarginAccount of liquidatee
# /// 5. `[writable]` in_vault_acc - Mango vault of in_token
# /// 6. `[writable]` out_vault_acc - Mango vault of out_token
# /// 7. `[]` signer_acc
# /// 8. `[]` token_prog_acc - Token program id
# /// 9. `[]` clock_acc - Clock sysvar account
# /// 10..10+NUM_MARKETS `[]` open_orders_accs - open orders for each of the spot market
# /// 10+NUM_MARKETS..10+2*NUM_MARKETS `[]`
# ///     oracle_accs - flux aggregator feed accounts
# ```
#
# ```
# pub fn partial_liquidate(
#     program_id: &Pubkey,
#     mango_group_pk: &Pubkey,
#     liqor_pk: &Pubkey,
#     liqor_in_token_pk: &Pubkey,
#     liqor_out_token_pk: &Pubkey,
#     liqee_margin_account_acc: &Pubkey,
#     in_vault_pk: &Pubkey,
#     out_vault_pk: &Pubkey,
#     signer_pk: &Pubkey,
#     open_orders_pks: &[Pubkey],
#     oracle_pks: &[Pubkey],
#     max_deposit: u64
# ) -> Result<Instruction, ProgramError>
# ```
#
# ## Client API call
#
# This is how it is built using the Mango Markets client API:
# ```
#   const keys = [
#     { isSigner: false, isWritable: true, pubkey: mangoGroup },
#     { isSigner: true, isWritable: false, pubkey: liqor },
#     { isSigner: false, isWritable: true, pubkey: liqorInTokenWallet },
#     { isSigner: false, isWritable: true, pubkey: liqorOutTokenWallet },
#     { isSigner: false, isWritable: true, pubkey: liqeeMarginAccount },
#     { isSigner: false, isWritable: true, pubkey: inTokenVault },
#     { isSigner: false, isWritable: true, pubkey: outTokenVault },
#     { isSigner: false, isWritable: false, pubkey: signerKey },
#     { isSigner: false, isWritable: false, pubkey: TOKEN_PROGRAM_ID },
#     { isSigner: false, isWritable: false, pubkey: SYSVAR_CLOCK_PUBKEY },
#     ...openOrders.map((pubkey) => ({
#       isSigner: false,
#       isWritable: false,
#       pubkey,
#     })),
#     ...oracles.map((pubkey) => ({
#       isSigner: false,
#       isWritable: false,
#       pubkey,
#     })),
#   ];
#   const data = encodeMangoInstruction({ PartialLiquidate: { maxDeposit } });
#
#   return new TransactionInstruction({ keys, data, programId });
# ```
#
# ## from_margin_account_and_market() function
#
# `from_margin_account_and_market()` merits a bit of explaining.
#
# `from_margin_account_and_market()` takes (among other things) a `Wallet` and a
# `MarginAccount`. The idea is that the `MarginAccount` has some assets in one token, and
# some liabilities in some different token.
#
# To liquidate the account, we want to:
# * supply tokens from the `Wallet` in the token currency that has the greatest liability
#   value in the `MarginAccount`
# * receive tokens in the `Wallet` in the token currency that has the greatest asset value
#   in the `MarginAccount`
#
# So we calculate the token currencies from the largest liabilities and assets in the
# `MarginAccount`, but we use those token types to get the correct `Wallet` accounts.
# * `input_token` is the `BasketToken` of the currency the `Wallet` is _paying_ and the
#   `MarginAccount` is _receiving_ to pay off its largest liability.
# * `output_token` is the `BasketToken` of the currency the `Wallet` is _receiving_ and the
#   `MarginAccount` is _paying_ from its largest asset.
#


class LiquidateInstructionBuilder(InstructionBuilder):
    def __init__(self, context: Context, group: Group, wallet: Wallet, margin_account: MarginAccount, oracles: typing.List[PublicKey], input_token: BasketToken, output_token: BasketToken, wallet_input_token_account: TokenAccount, wallet_output_token_account: TokenAccount, maximum_input_amount: Decimal):
        super().__init__(context)
        self.group: Group = group
        self.wallet: Wallet = wallet
        self.margin_account: MarginAccount = margin_account
        self.oracles: typing.List[PublicKey] = oracles
        self.input_token: BasketToken = input_token
        self.output_token: BasketToken = output_token
        self.wallet_input_token_account: TokenAccount = wallet_input_token_account
        self.wallet_output_token_account: TokenAccount = wallet_output_token_account
        self.maximum_input_amount: Decimal = maximum_input_amount

    def build(self) -> TransactionInstruction:
        transaction = TransactionInstruction(
            keys=[
                AccountMeta(is_signer=False, is_writable=True, pubkey=self.group.address),
                AccountMeta(is_signer=True, is_writable=False, pubkey=self.wallet.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=self.wallet_input_token_account.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=self.wallet_output_token_account.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=self.margin_account.address),
                AccountMeta(is_signer=False, is_writable=True, pubkey=self.input_token.vault),
                AccountMeta(is_signer=False, is_writable=True, pubkey=self.output_token.vault),
                AccountMeta(is_signer=False, is_writable=False, pubkey=self.group.signer_key),
                AccountMeta(is_signer=False, is_writable=False, pubkey=TOKEN_PROGRAM_ID),
                AccountMeta(is_signer=False, is_writable=False, pubkey=SYSVAR_CLOCK_PUBKEY),
                *list([AccountMeta(is_signer=False, is_writable=True, pubkey=oo_address)
                      for oo_address in self.margin_account.open_orders]),
                *list([AccountMeta(is_signer=False, is_writable=False, pubkey=oracle_address) for oracle_address in self.oracles])
            ],
            program_id=self.context.program_id,
            data=layouts.PARTIAL_LIQUIDATE.build({"max_deposit": int(self.maximum_input_amount)})
        )
        self.logger.debug(f"Built transaction: {transaction}")
        return transaction

    @classmethod
    def from_margin_account_and_market(cls, context: Context, group: Group, wallet: Wallet, margin_account: MarginAccount, prices: typing.List[TokenValue]) -> typing.Optional["LiquidateInstructionBuilder"]:
        logger: logging.Logger = logging.getLogger(cls.__name__)

        oracles = list([mkt.oracle for mkt in group.markets])

        balance_sheets = margin_account.get_priced_balance_sheets(group, prices)

        sorted_by_assets = sorted(balance_sheets, key=lambda sheet: sheet.assets, reverse=True)
        sorted_by_liabilities = sorted(balance_sheets, key=lambda sheet: sheet.liabilities, reverse=True)

        most_assets = sorted_by_assets[0]
        most_liabilities = sorted_by_liabilities[0]
        if most_assets.token == most_liabilities.token:
            # If there's a weirdness where the account with the biggest assets is also the one
            # with the biggest liabilities, pick the next-best one by assets.
            logger.info(
                f"Switching asset token from {most_assets.token.name} to {sorted_by_assets[1].token.name} because {most_liabilities.token.name} is the token with most liabilities.")
            most_assets = sorted_by_assets[1]

        logger.info(f"Most assets: {most_assets}")
        logger.info(f"Most liabilities: {most_liabilities}")

        most_assets_basket_token = BasketToken.find_by_token(group.basket_tokens, most_assets.token)
        most_liabilities_basket_token = BasketToken.find_by_token(group.basket_tokens, most_liabilities.token)
        logger.info(f"Most assets basket token: {most_assets_basket_token}")
        logger.info(f"Most liabilities basket token: {most_liabilities_basket_token}")

        if most_assets.value == Decimal(0):
            logger.warning(f"Margin account {margin_account.address} has no assets to take.")
            return None

        if most_liabilities.value == Decimal(0):
            logger.warning(f"Margin account {margin_account.address} has no liabilities to fund.")
            return None

        wallet_input_token_account = TokenAccount.fetch_largest_for_owner_and_token(
            context, wallet.address, most_liabilities.token)
        if wallet_input_token_account is None:
            raise Exception(f"Could not load wallet input token account for mint '{most_liabilities.token.mint}'")

        if wallet_input_token_account.value.value == Decimal(0):
            logger.warning(
                f"Wallet token account {wallet_input_token_account.address} has no tokens to send that could fund a liquidation.")
            return None

        wallet_output_token_account = TokenAccount.fetch_largest_for_owner_and_token(
            context, wallet.address, most_assets.token)
        if wallet_output_token_account is None:
            raise Exception(f"Could not load wallet output token account for mint '{most_assets.token.mint}'")

        return LiquidateInstructionBuilder(context, group, wallet, margin_account, oracles,
                                           most_liabilities_basket_token, most_assets_basket_token,
                                           wallet_input_token_account,
                                           wallet_output_token_account,
                                           wallet_input_token_account.value.value)

    def __str__(self) -> str:
        # Print the members out using the Rust parameter order and names.
        return f"""« LiquidateInstructionBuilder:
    program_id: &Pubkey: {self.context.program_id},
    mango_group_pk: &Pubkey: {self.group.address},
    liqor_pk: &Pubkey: {self.wallet.address},
    liqor_in_token_pk: &Pubkey: {self.wallet_input_token_account.address},
    liqor_out_token_pk: &Pubkey: {self.wallet_output_token_account.address},
    liqee_margin_account_acc: &Pubkey: {self.margin_account.address},
    in_vault_pk: &Pubkey: {self.input_token.vault},
    out_vault_pk: &Pubkey: {self.output_token.vault},
    signer_pk: &Pubkey: {self.group.signer_key},
    open_orders_pks: &[Pubkey]: {self.margin_account.open_orders},
    oracle_pks: &[Pubkey]: {self.oracles},
    max_deposit: u64: : {self.maximum_input_amount}
»"""


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
        minimum_balance_response = self.context.client.get_minimum_balance_for_rent_exemption(ACCOUNT_LEN)
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
        response = self.context.client.get_minimum_balance_for_rent_exemption(layouts.OPEN_ORDERS.sizeof())
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
    def __init__(self, context: Context, wallet: Wallet, market: Market, source: PublicKey, open_orders_address: PublicKey, order_type: OrderType, side: Side, price: Decimal, quantity: Decimal, client_id: int):
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

    def build(self) -> TransactionInstruction:
        instruction = self.market.make_place_order_instruction(
            self.source,
            self.wallet.account,
            self.order_type,
            self.side,
            float(self.price),
            float(self.quantity),
            self.client_id,
            self.open_orders_address
            # fee_discount_pubkey: PublicKey = None,
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
»"""


# # 🥭 ConsumeEventsInstructionBuilder class
#
# Creates an event-consuming 'crank' instruction.
#
class ConsumeEventsInstructionBuilder(InstructionBuilder):
    def __init__(self, context: Context, wallet: Wallet, market: Market, open_orders_addresses: typing.List[PublicKey], limit: int = 32):
        super().__init__(context)
        self.wallet: Wallet = wallet
        self.market: Market = market
        self.open_orders_addresses: typing.List[PublicKey] = open_orders_addresses
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
