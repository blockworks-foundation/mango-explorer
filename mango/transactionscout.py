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
from .instrumentvalue import InstrumentValue
from .mangoinstruction import MangoInstruction
from .layouts import layouts
from .ownedinstrumentvalue import OwnedInstrumentValue


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


# # 🥭 TransactionScout class
#
class TransactionScout:
    def __init__(self, timestamp: datetime.datetime, signatures: typing.Sequence[str],
                 succeeded: bool, group_name: str, accounts: typing.Sequence[PublicKey],
                 instructions: typing.Sequence[MangoInstruction], messages: typing.Sequence[str],
                 pre_token_balances: typing.Sequence[OwnedInstrumentValue],
                 post_token_balances: typing.Sequence[OwnedInstrumentValue]) -> None:
        self.timestamp: datetime.datetime = timestamp
        self.signatures: typing.Sequence[str] = signatures
        self.succeeded: bool = succeeded
        self.group_name: str = group_name
        self.accounts: typing.Sequence[PublicKey] = accounts
        self.instructions: typing.Sequence[MangoInstruction] = instructions
        self.messages: typing.Sequence[str] = messages
        self.pre_token_balances: typing.Sequence[OwnedInstrumentValue] = pre_token_balances
        self.post_token_balances: typing.Sequence[OwnedInstrumentValue] = post_token_balances

    @property
    def summary(self) -> str:
        result = "[Success]" if self.succeeded else "[Failed]"
        instructions = ", ".join([ins.instruction_type.name for ins in self.instructions])
        changes = OwnedInstrumentValue.changes(self.pre_token_balances, self.post_token_balances)

        in_tokens = []
        for ins in self.instructions:
            if ins.token_in_account is not None:
                in_tokens += [OwnedInstrumentValue.find_by_owner(changes, ins.token_in_account)]

        out_tokens = []
        for ins in self.instructions:
            if ins.token_out_account is not None:
                out_tokens += [OwnedInstrumentValue.find_by_owner(changes, ins.token_out_account)]

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
        transaction_details = context.client.get_confirmed_transaction(signature)
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
    def from_transaction_response(context: Context, response: typing.Dict[str, typing.Any]) -> "TransactionScout":
        def balance_to_token_value(accounts: typing.Sequence[PublicKey], balance: typing.Dict[str, typing.Any]) -> OwnedInstrumentValue:
            mint = PublicKey(balance["mint"])
            account = accounts[balance["accountIndex"]]
            amount = Decimal(balance["uiTokenAmount"]["amount"])
            decimals = Decimal(balance["uiTokenAmount"]["decimals"])
            divisor = Decimal(10) ** decimals
            value = amount / divisor
            token = context.instrument_lookup.find_by_mint_or_raise(mint)
            return OwnedInstrumentValue(account, InstrumentValue(token, value))

        try:
            succeeded = True if response["meta"]["err"] is None else False
            accounts = list(map(PublicKey, response["transaction"]["message"]["accountKeys"]))
            instructions: typing.List[MangoInstruction] = []
            for instruction_data in response["transaction"]["message"]["instructions"]:
                instruction = mango_instruction_from_response(context, accounts, instruction_data)
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
        def format_tokens(account_token_values: typing.Sequence[OwnedInstrumentValue]) -> str:
            if len(account_token_values) == 0:
                return "None"
            return "\n        ".join([f"{atv}" for atv in account_token_values])

        instruction_names = ", ".join([ins.instruction_type.name for ins in self.instructions])
        signatures = "\n        ".join(self.signatures)
        accounts = "\n        ".join([f"{acc}" for acc in self.accounts])
        messages = "\n        ".join(self.messages)
        instructions = "\n        ".join([f"{ins}" for ins in self.instructions])
        changes = OwnedInstrumentValue.changes(self.pre_token_balances, self.post_token_balances)
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
def fetch_all_recent_transaction_signatures(context: Context) -> typing.Sequence[str]:
    all_fetched = False
    before = None
    signature_results: typing.List[str] = []
    while not all_fetched:
        signatures = context.client.get_confirmed_signatures_for_address2(context.group_address, before=before)
        signature_results += signatures
        if (len(signatures) == 0):
            all_fetched = True
        else:
            before = signature_results[-1]

    return signature_results


def mango_instruction_from_response(context: Context, all_accounts: typing.Sequence[PublicKey], instruction_data: typing.Dict[str, typing.Any]) -> typing.Optional["MangoInstruction"]:
    program_account_index = instruction_data["programIdIndex"]
    if all_accounts[program_account_index] != context.mango_program_address:
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
