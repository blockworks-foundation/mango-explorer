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


import base58
import datetime
import logging
import traceback
import typing

from decimal import Decimal
from solana.publickey import PublicKey

from .context import Context
from .instructiontype import InstructionType
from .layouts import layouts
from .orders import OrderType, Side
from .ownedtokenvalue import OwnedTokenValue
from .tokenvalue import TokenValue


# # 🥭 TransactionScout
#
# ## Transaction Indices
#
# Transactions come with a large account list.
#
# Instructions, individually, take accounts.
#
# The accounts instructions take are listed in the the transaction's list of accounts.
#
# The instruction data therefore doesn't need to specify account public keys, only the
# index of those public keys in the main transaction's list.
#
# So, for example, if an instruction uses 3 accounts, the instruction data could say
# [3, 2, 14], meaning the first account it uses is index 3 in the whole transaction account
# list, the second is index 2 in the whole transaction account list, the third is index 14
# in the whole transaction account list.
#
# This complicates figuring out which account is which for a given instruction, especially
# since some of the accounts (like the sender/signer account) can appear at different
# indices depending on which instruction is being used.
#
# We keep a few static dictionaries here to allow us to dereference important accounts per
# type.
#
# In addition, we dereference the accounts for each instruction when we instantiate each
# `MangoInstruction`, so users of `MangoInstruction` don't need to worry about
# these details.
#


# The index of the sender/signer depends on the instruction.
_instruction_signer_indices: typing.Dict[InstructionType, int] = {
    InstructionType.InitMangoGroup: 1,
    InstructionType.InitMarginAccount: 2,
    InstructionType.Deposit: 2,
    InstructionType.Withdraw: 2,
    InstructionType.AddSpotMarket: 7,
    InstructionType.AddToBasket: 2,
    InstructionType.Borrow: 2,
    InstructionType.CachePrices: -1,  # No signer
    InstructionType.CacheRootBanks: -1,  # No signer
    InstructionType.PlaceSpotOrder: 2,
    InstructionType.AddOracle: 2,
    InstructionType.AddPerpMarket: 6,
    InstructionType.PlacePerpOrder: 2,
    InstructionType.CancelPerpOrderByClientId: 2,
    InstructionType.CancelPerpOrder: 2,
    InstructionType.ConsumeEvents: -1,  # No signer
    InstructionType.CachePerpMarkets: -1,  # No signer
    InstructionType.UpdateFunding: -1,  # No signer
    InstructionType.SetOracle: -1,  # No signer
    InstructionType.SettleFunds: 2,
    InstructionType.CancelSpotOrder: 1,
    InstructionType.UpdateRootBank: -1,  # No signer
    InstructionType.SettlePnl: -1,  # No signer
    InstructionType.SettleBorrow: -1  # No signer
}

# The index of the token IN account depends on the instruction, and for some instructions
# doesn't exist.
_token_in_indices: typing.Dict[InstructionType, int] = {
    InstructionType.InitMangoGroup: -1,
    InstructionType.InitMarginAccount: -1,
    InstructionType.Deposit: 8,
    InstructionType.Withdraw: 7,
    InstructionType.AddSpotMarket: -1,
    InstructionType.AddToBasket: -1,
    InstructionType.Borrow: -1,
    InstructionType.CachePrices: -1,
    InstructionType.CacheRootBanks: -1,
    InstructionType.PlaceSpotOrder: -1,
    InstructionType.AddOracle: -1,
    InstructionType.AddPerpMarket: -1,
    InstructionType.PlacePerpOrder: -1,
    InstructionType.CancelPerpOrderByClientId: -1,
    InstructionType.CancelPerpOrder: -1,
    InstructionType.ConsumeEvents: -1,
    InstructionType.CachePerpMarkets: -1,
    InstructionType.UpdateFunding: -1,
    InstructionType.SetOracle: -1,
    InstructionType.SettleFunds: -1,
    InstructionType.CancelSpotOrder: -1,
    InstructionType.UpdateRootBank: -1,
    InstructionType.SettlePnl: -1,
    InstructionType.SettleBorrow: -1,
}

# The index of the token OUT account depends on the instruction, and for some instructions
# doesn't exist.
_token_out_indices: typing.Dict[InstructionType, int] = {
    InstructionType.InitMangoGroup: -1,
    InstructionType.InitMarginAccount: -1,
    InstructionType.Deposit: 6,
    InstructionType.Withdraw: 6,
    InstructionType.AddSpotMarket: -1,
    InstructionType.AddToBasket: -1,
    InstructionType.Borrow: -1,
    InstructionType.CachePrices: -1,
    InstructionType.CacheRootBanks: -1,
    InstructionType.PlaceSpotOrder: -1,
    InstructionType.AddOracle: -1,
    InstructionType.AddPerpMarket: -1,
    InstructionType.PlacePerpOrder: -1,
    InstructionType.CancelPerpOrderByClientId: -1,
    InstructionType.CancelPerpOrder: -1,
    InstructionType.ConsumeEvents: -1,
    InstructionType.CachePerpMarkets: -1,
    InstructionType.UpdateFunding: -1,
    InstructionType.SetOracle: -1,
    InstructionType.SettleFunds: -1,
    InstructionType.CancelSpotOrder: -1,
    InstructionType.UpdateRootBank: -1,
    InstructionType.SettlePnl: -1,
    InstructionType.SettleBorrow: -1,
}


# Some instructions (like liqudate) have a 'target' account. Most don't.
_target_indices: typing.Dict[InstructionType, int] = {
    InstructionType.InitMangoGroup: -1,
    InstructionType.InitMarginAccount: -1,
    InstructionType.Deposit: -1,
    InstructionType.Withdraw: -1,
    InstructionType.AddSpotMarket: -1,
    InstructionType.AddToBasket: -1,
    InstructionType.Borrow: -1,
    InstructionType.CachePrices: -1,
    InstructionType.CacheRootBanks: -1,
    InstructionType.PlaceSpotOrder: -1,
    InstructionType.AddOracle: -1,
    InstructionType.AddPerpMarket: -1,
    InstructionType.PlacePerpOrder: -1,
    InstructionType.CancelPerpOrderByClientId: -1,
    InstructionType.CancelPerpOrder: -1,
    InstructionType.ConsumeEvents: -1,
    InstructionType.CachePerpMarkets: -1,
    InstructionType.UpdateFunding: -1,
    InstructionType.SetOracle: -1,
    InstructionType.SettleFunds: -1,
    InstructionType.CancelSpotOrder: -1,
    InstructionType.UpdateRootBank: -1,
    InstructionType.SettlePnl: -1,
    InstructionType.SettleBorrow: -1,
}


# # 🥭 MangoInstruction class
#
# This class packages up Mango instruction data, which can come from disparate parts of the
# transaction. Keeping it all together here makes many things simpler.
#
class MangoInstruction:
    def __init__(self, instruction_type: InstructionType, instruction_data: typing.Any, accounts: typing.Sequence[PublicKey]):
        self.instruction_type = instruction_type
        self.instruction_data = instruction_data
        self.accounts = accounts

    @property
    def group(self) -> PublicKey:
        # Group PublicKey is always the zero index.
        return self.accounts[0]

    @property
    def sender(self) -> typing.Optional[PublicKey]:
        account_index = _instruction_signer_indices[self.instruction_type]
        if account_index < 0:
            return None
        return self.accounts[account_index]

    @property
    def token_in_account(self) -> typing.Optional[PublicKey]:
        account_index = _token_in_indices[self.instruction_type]
        if account_index < 0:
            return None
        return self.accounts[account_index]

    @property
    def token_out_account(self) -> typing.Optional[PublicKey]:
        account_index = _token_out_indices[self.instruction_type]
        if account_index < 0:
            return None
        return self.accounts[account_index]

    @property
    def target_account(self) -> typing.Optional[PublicKey]:
        account_index = _target_indices[self.instruction_type]
        if account_index < 0:
            return None
        return self.accounts[account_index]

    def describe_parameters(self) -> str:
        instruction_type = self.instruction_type
        additional_data = ""
        if instruction_type == InstructionType.InitMangoGroup:
            pass
        elif instruction_type == InstructionType.InitMarginAccount:
            pass
        elif instruction_type == InstructionType.Deposit:
            additional_data = f"quantity: {self.instruction_data.quantity}"
        elif instruction_type == InstructionType.Withdraw:
            additional_data = f"quantity: {self.instruction_data.quantity}, allow_borrow: {self.instruction_data.allow_borrow}"
        elif instruction_type == InstructionType.AddSpotMarket:
            pass
        elif instruction_type == InstructionType.AddToBasket:
            pass
        elif instruction_type == InstructionType.Borrow:
            pass
        elif instruction_type == InstructionType.CachePrices:
            pass
        elif instruction_type == InstructionType.CacheRootBanks:
            pass
        elif instruction_type == InstructionType.PlaceSpotOrder:
            additional_data = f"side: {Side.from_value(self.instruction_data.side)}, order_type: {OrderType.from_value(self.instruction_data.order_type)}, limit_price: {self.instruction_data.limit_price}, max_base_quantity: {self.instruction_data.max_base_quantity}, max_quote_quantity: {self.instruction_data.max_quote_quantity}, self_trade_behavior: {self.instruction_data.self_trade_behavior}, client_id: {self.instruction_data.client_id}, limit: {self.instruction_data.limit}"
        elif instruction_type == InstructionType.AddOracle:
            pass
        elif instruction_type == InstructionType.AddPerpMarket:
            pass
        elif instruction_type == InstructionType.PlacePerpOrder:
            additional_data = f"side: {Side.from_value(self.instruction_data.side)}, order_type: {OrderType.from_value(self.instruction_data.order_type)}, price: {self.instruction_data.price}, quantity: {self.instruction_data.quantity}, client_order_id: {self.instruction_data.client_order_id}"
        elif instruction_type == InstructionType.CancelPerpOrderByClientId:
            additional_data = f"client ID: {self.instruction_data.client_order_id}"
        elif instruction_type == InstructionType.CancelPerpOrder:
            additional_data = f"order ID: {self.instruction_data.order_id}, side: {Side.from_value(self.instruction_data.side)}"
        elif instruction_type == InstructionType.ConsumeEvents:
            additional_data = f"limit: {self.instruction_data.limit}"
        elif instruction_type == InstructionType.CachePerpMarkets:
            pass
        elif instruction_type == InstructionType.UpdateFunding:
            pass
        elif instruction_type == InstructionType.SetOracle:
            pass
        elif instruction_type == InstructionType.SettleFunds:
            pass
        elif instruction_type == InstructionType.CancelSpotOrder:
            additional_data = f"order ID: {self.instruction_data.order_id}, side: {Side.from_value(self.instruction_data.side)}"
        elif instruction_type == InstructionType.UpdateRootBank:
            pass
        elif instruction_type == InstructionType.SettlePnl:
            pass
        elif instruction_type == InstructionType.SettleBorrow:
            pass

        return additional_data

    @staticmethod
    def from_response(context: Context, all_accounts: typing.Sequence[PublicKey], instruction_data: typing.Dict) -> typing.Optional["MangoInstruction"]:
        program_account_index = instruction_data["programIdIndex"]
        if all_accounts[program_account_index] != context.program_id:
            # It's an instruction, it's just not a Mango one.
            return None

        data = instruction_data["data"]
        instructions_account_indices = instruction_data["accounts"]

        decoded = base58.b58decode(data)
        initial = layouts.MANGO_INSTRUCTION_VARIANT_FINDER.parse(decoded)
        parser = layouts.InstructionParsersByVariant[initial.variant]
        if parser is None:
            logging.warning(
                f"Could not find instruction parser for variant {initial.variant} / {InstructionType(initial.variant)}.")
            return None

        # A whole bunch of accounts are listed for a transaction. Some (or all) of them apply
        # to this instruction. The instruction data gives the index of each account it uses,
        # in the order in which it uses them. So, for example, if it uses 3 accounts, the
        # instruction data could say [3, 2, 14], meaning the first account it uses is index 3
        # in the whole transaction account list, the second is index 2 in the whole transaction
        # account list, the third is index 14 in the whole transaction account list.
        accounts: typing.List[PublicKey] = []
        for index in instructions_account_indices:
            accounts += [all_accounts[index]]

        parsed = parser.parse(decoded)
        instruction_type = InstructionType(int(parsed.variant))

        return MangoInstruction(instruction_type, parsed, accounts)

    @staticmethod
    def _order_type_enum(side: Decimal):
        return Side.BUY if side == Decimal(0) else Side.SELL

    def __str__(self) -> str:
        parameters = self.describe_parameters() or "None"
        return f"« {self.instruction_type.name}: {parameters} »"

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 TransactionScout class
#


class TransactionScout:
    def __init__(self, timestamp: datetime.datetime, signatures: typing.Sequence[str],
                 succeeded: bool, group_name: str, accounts: typing.Sequence[PublicKey],
                 instructions: typing.Sequence[MangoInstruction], messages: typing.Sequence[str],
                 pre_token_balances: typing.Sequence[OwnedTokenValue],
                 post_token_balances: typing.Sequence[OwnedTokenValue]):
        self.timestamp: datetime.datetime = timestamp
        self.signatures: typing.Sequence[str] = signatures
        self.succeeded: bool = succeeded
        self.group_name: str = group_name
        self.accounts: typing.Sequence[PublicKey] = accounts
        self.instructions: typing.Sequence[MangoInstruction] = instructions
        self.messages: typing.Sequence[str] = messages
        self.pre_token_balances: typing.Sequence[OwnedTokenValue] = pre_token_balances
        self.post_token_balances: typing.Sequence[OwnedTokenValue] = post_token_balances

    @property
    def summary(self) -> str:
        result = "[Success]" if self.succeeded else "[Failed]"
        instructions = ", ".join([ins.instruction_type.name for ins in self.instructions])
        changes = OwnedTokenValue.changes(self.pre_token_balances, self.post_token_balances)

        in_tokens = []
        for ins in self.instructions:
            if ins.token_in_account is not None:
                in_tokens += [OwnedTokenValue.find_by_owner(changes, ins.token_in_account)]

        out_tokens = []
        for ins in self.instructions:
            if ins.token_out_account is not None:
                out_tokens += [OwnedTokenValue.find_by_owner(changes, ins.token_out_account)]

        changed_tokens = in_tokens + out_tokens
        changed_tokens_text = ", ".join(
            [f"{tok.token_value.value:,.8f} {tok.token_value.token.name}" for tok in changed_tokens]) or "None"

        return f"« TransactionScout {result} {self.group_name} [{self.timestamp}] {instructions}: Token Changes: {changed_tokens_text}\n    {self.signatures} »"

    @property
    def sender(self) -> typing.Optional[PublicKey]:
        return self.instructions[0].sender

    @property
    def group(self) -> PublicKey:
        return self.instructions[0].group

    def has_any_instruction_of_type(self, instruction_type: InstructionType) -> bool:
        return any(map(lambda ins: ins.instruction_type == instruction_type, self.instructions))

    @staticmethod
    def load_if_available(context: Context, signature: str) -> typing.Optional["TransactionScout"]:
        transaction_response = context.client.get_confirmed_transaction(signature)
        transaction_details = context.unwrap_or_raise_exception(transaction_response)
        if transaction_details is None:
            return None
        return TransactionScout.from_transaction_response(context, transaction_details)

    @staticmethod
    def load(context: Context, signature: str) -> "TransactionScout":
        tx = TransactionScout.load_if_available(context, signature)
        if tx is None:
            raise Exception(f"Transaction '{signature}' not found.")
        return tx

    @staticmethod
    def from_transaction_response(context: Context, response: typing.Dict) -> "TransactionScout":
        def balance_to_token_value(accounts: typing.Sequence[PublicKey], balance: typing.Dict) -> OwnedTokenValue:
            mint = PublicKey(balance["mint"])
            account = accounts[balance["accountIndex"]]
            amount = Decimal(balance["uiTokenAmount"]["amount"])
            decimals = Decimal(balance["uiTokenAmount"]["decimals"])
            divisor = Decimal(10) ** decimals
            value = amount / divisor
            token = context.token_lookup.find_by_mint_or_raise(mint)
            return OwnedTokenValue(account, TokenValue(token, value))

        try:
            succeeded = True if response["meta"]["err"] is None else False
            accounts = list(map(PublicKey, response["transaction"]["message"]["accountKeys"]))
            instructions: typing.List[MangoInstruction] = []
            for instruction_data in response["transaction"]["message"]["instructions"]:
                instruction = MangoInstruction.from_response(context, accounts, instruction_data)
                if instruction is not None:
                    instructions += [instruction]

            group_name = context.lookup_group_name(instructions[0].group)
            timestamp = datetime.datetime.fromtimestamp(response["blockTime"])
            signatures = response["transaction"]["signatures"]
            messages = response["meta"]["logMessages"]
            pre_token_balances = list(map(lambda bal: balance_to_token_value(
                accounts, bal), response["meta"]["preTokenBalances"]))
            post_token_balances = list(map(lambda bal: balance_to_token_value(
                accounts, bal), response["meta"]["postTokenBalances"]))
            return TransactionScout(timestamp,
                                    signatures,
                                    succeeded,
                                    group_name,
                                    accounts,
                                    instructions,
                                    messages,
                                    pre_token_balances,
                                    post_token_balances)
        except Exception as exception:
            signature = "Unknown"
            if response and ("transaction" in response) and ("signatures" in response["transaction"]) and len(response["transaction"]["signatures"]) > 0:
                signature = ", ".join(response["transaction"]["signatures"])
            raise Exception(f"Exception fetching transaction '{signature}' - {traceback.format_exc()}", exception)

    def __str__(self) -> str:
        def format_tokens(account_token_values: typing.Sequence[OwnedTokenValue]) -> str:
            if len(account_token_values) == 0:
                return "None"
            return "\n        ".join([f"{atv}" for atv in account_token_values])

        instruction_names = ", ".join([ins.instruction_type.name for ins in self.instructions])
        signatures = "\n        ".join(self.signatures)
        accounts = "\n        ".join([f"{acc}" for acc in self.accounts])
        messages = "\n        ".join(self.messages)
        instructions = "\n        ".join([f"{ins}" for ins in self.instructions])
        changes = OwnedTokenValue.changes(self.pre_token_balances, self.post_token_balances)
        tokens_in = format_tokens(self.pre_token_balances)
        tokens_out = format_tokens(self.post_token_balances)
        token_changes = format_tokens(changes)
        return f"""« TransactionScout {self.timestamp}: {instruction_names}
    Sender:
        {self.sender}
    Succeeded:
        {self.succeeded}
    Group:
        {self.group_name} [{self.group}]
    Signatures:
        {signatures}
    Instructions:
        {instructions}
    Accounts:
        {accounts}
    Messages:
        {messages}
    Tokens In:
        {tokens_in}
    Tokens Out:
        {tokens_out}
    Token Changes:
        {token_changes}
»"""

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 fetch_all_recent_transaction_signatures function
#

def fetch_all_recent_transaction_signatures(context: Context, in_the_last: datetime.timedelta = datetime.timedelta(days=1)) -> typing.Sequence[str]:
    now = datetime.datetime.now()
    recency_cutoff = now - in_the_last
    recency_cutoff_timestamp = recency_cutoff.timestamp()

    all_fetched = False
    before = None
    signature_results = []
    while not all_fetched:
        signature_response = context.client.get_confirmed_signature_for_address2(context.group_id, before=before)
        signature_result = context.unwrap_or_raise_exception(signature_response)
        signature_results += signature_result
        if (len(signature_result) == 0) or (signature_result[-1]["blockTime"] < recency_cutoff_timestamp):
            all_fetched = True
        else:
            before = signature_results[-1]["signature"]

    recent = [result["signature"] for result in signature_results if result["blockTime"] > recency_cutoff_timestamp]
    return recent
