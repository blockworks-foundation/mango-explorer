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

import logging
import typing

from solana.account import Account as SolanaAccount
from solana.blockhash import Blockhash
from solana.publickey import PublicKey
from solana.transaction import Transaction, TransactionInstruction

from .context import Context
from .wallet import Wallet

_MAXIMUM_TRANSACTION_LENGTH = 1280 - 40 - 8
_SIGNATURE_LENGTH = 64


# 🥭 CombinableInstructions class
#
# This class wraps up zero or more Solana instructions and signers, and allows instances to be combined
# easily into a single instance. This instance can then be executed.
#
# This allows simple uses like, for example:
# ```
# (signers + place_orders + settle + crank).execute(context)
# ```
#

class CombinableInstructions():
    def __init__(self, signers: typing.Sequence[SolanaAccount], instructions: typing.Sequence[TransactionInstruction]):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.signers: typing.Sequence[SolanaAccount] = signers
        self.instructions: typing.Sequence[TransactionInstruction] = instructions

    @staticmethod
    def empty() -> "CombinableInstructions":
        return CombinableInstructions(signers=[], instructions=[])

    @staticmethod
    def from_signers(signers: typing.Sequence[SolanaAccount]) -> "CombinableInstructions":
        return CombinableInstructions(signers=signers, instructions=[])

    @staticmethod
    def from_wallet(wallet: Wallet) -> "CombinableInstructions":
        return CombinableInstructions(signers=[wallet.account], instructions=[])

    @staticmethod
    def from_instruction(instruction: TransactionInstruction) -> "CombinableInstructions":
        return CombinableInstructions(signers=[], instructions=[instruction])

    # This is a quick-and-dirty way to find out the size the transaction will be. There's an upper limit
    # on transaction size of 1232 so we need to keep all transactions below this size.
    @staticmethod
    def transaction_size(signers: typing.Sequence[SolanaAccount], instructions: typing.Sequence[TransactionInstruction]) -> int:
        inspector = Transaction()
        inspector.recent_blockhash = Blockhash(str(PublicKey(3)))
        inspector.instructions.extend(instructions)
        inspector.sign(*signers)
        signed_data = inspector.serialize_message()

        length: int = len(signed_data)

        # Signature count length
        length += 1

        # Signatures
        length += (len(inspector.signatures) * _SIGNATURE_LENGTH)

        return length

    def __add__(self, new_instruction_data: "CombinableInstructions") -> "CombinableInstructions":
        all_signers = [*self.signers, *new_instruction_data.signers]
        all_instructions = [*self.instructions, *new_instruction_data.instructions]
        return CombinableInstructions(signers=all_signers, instructions=all_instructions)

    def execute(self, context: Context) -> typing.Any:
        vetted_chunks: typing.List[typing.List[TransactionInstruction]] = []
        current_chunk: typing.List[TransactionInstruction] = []
        for instruction in self.instructions:
            instruction_size_on_its_own = CombinableInstructions.transaction_size(self.signers, [instruction])
            if instruction_size_on_its_own >= _MAXIMUM_TRANSACTION_LENGTH:
                raise Exception(
                    f"Instruction exceeds maximum size - creates a transaction {instruction_size_on_its_own} bytes long. {instruction}")

            in_progress_chunk = current_chunk + [instruction]
            transaction_size = CombinableInstructions.transaction_size(self.signers, in_progress_chunk)
            if transaction_size < _MAXIMUM_TRANSACTION_LENGTH:
                current_chunk = in_progress_chunk
            else:
                vetted_chunks += [current_chunk]
                current_chunk = [instruction]

        all_chunks = vetted_chunks + [current_chunk]

        if len(all_chunks) == 1 and len(all_chunks[0]) == 0:
            self.logger.info("No instructions to run.")
            return []

        if len(all_chunks) > 1:
            self.logger.info(f"Running instructions in {len(all_chunks)} transactions.")

        total_in_chunks = sum(map(lambda chunk: len(chunk), all_chunks))
        if total_in_chunks != len(self.instructions):
            raise Exception(
                f"Failed to chunk instructions. Have {total_in_chunks} instuctions in chunks. Should have {len(self.instructions)}.")

        results = []
        for chunk in all_chunks:
            transaction = Transaction()
            transaction.instructions.extend(chunk)
            response = context.client.send_transaction(transaction, *self.signers, opts=context.transaction_options)
            results += [context.unwrap_or_raise_exception(response)]

        return results

    def execute_and_unwrap_transaction_ids(self, context: Context) -> typing.Sequence[str]:
        return typing.cast(typing.Sequence[str], self.execute(context))

    def __str__(self) -> str:
        report: typing.List[str] = []
        for index, signer in enumerate(self.signers):
            report += [f"Signer[{index}]: {signer.public_key()}"]

        for index, instruction in enumerate(self.instructions):
            for index, key in enumerate(instruction.keys):
                report += [f"Key[{index}]: {key.pubkey} {key.is_signer: <5} {key.is_writable: <5}"]
            report += [f"Program ID: {instruction.program_id}"]
            report += ["Data: " + "".join("{:02x}".format(x) for x in instruction.data)]

        return "\n".join(report)

    def __repr__(self) -> str:
        return f"{self}"
