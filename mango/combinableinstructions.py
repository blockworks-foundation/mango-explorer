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

from solana.blockhash import Blockhash
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.transaction import Transaction, TransactionInstruction

from .context import Context
from .instructionreporter import InstructionReporter
from .wallet import Wallet

_MAXIMUM_TRANSACTION_LENGTH = 1280 - 40 - 8
_SIGNATURE_LENGTH = 64


def _split_instructions_into_chunks(context: Context, signers: typing.Sequence[Keypair], instructions: typing.Sequence[TransactionInstruction]) -> typing.Sequence[typing.Sequence[TransactionInstruction]]:
    vetted_chunks: typing.List[typing.List[TransactionInstruction]] = []
    current_chunk: typing.List[TransactionInstruction] = []
    for instruction in instructions:
        instruction_size_on_its_own = CombinableInstructions.transaction_size(signers, [instruction])
        if instruction_size_on_its_own >= _MAXIMUM_TRANSACTION_LENGTH:
            report = context.client.instruction_reporter.report(instruction)
            raise Exception(
                f"Instruction exceeds maximum size - creates a transaction {instruction_size_on_its_own} bytes long:\n{report}")

        in_progress_chunk = current_chunk + [instruction]
        transaction_size = CombinableInstructions.transaction_size(signers, in_progress_chunk)
        if transaction_size < _MAXIMUM_TRANSACTION_LENGTH:
            current_chunk = in_progress_chunk
        else:
            vetted_chunks += [current_chunk]
            current_chunk = [instruction]

    all_chunks = vetted_chunks + [current_chunk]

    total_in_chunks = sum(map(lambda chunk: len(chunk), all_chunks))
    if total_in_chunks != len(instructions):
        raise Exception(
            f"Failed to chunk instructions. Have {total_in_chunks} instuctions in chunks. Should have {len(instructions)}.")

    return all_chunks


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
    def __init__(self, signers: typing.Sequence[Keypair], instructions: typing.Sequence[TransactionInstruction]):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.signers: typing.Sequence[Keypair] = signers
        self.instructions: typing.Sequence[TransactionInstruction] = instructions

    @staticmethod
    def empty() -> "CombinableInstructions":
        return CombinableInstructions(signers=[], instructions=[])

    @staticmethod
    def from_signers(signers: typing.Sequence[Keypair]) -> "CombinableInstructions":
        return CombinableInstructions(signers=signers, instructions=[])

    @staticmethod
    def from_wallet(wallet: Wallet) -> "CombinableInstructions":
        return CombinableInstructions(signers=[wallet.keypair], instructions=[])

    @staticmethod
    def from_instruction(instruction: TransactionInstruction) -> "CombinableInstructions":
        return CombinableInstructions(signers=[], instructions=[instruction])

    # This is a quick-and-dirty way to find out the size the transaction will be. There's an upper limit
    # on transaction size of 1232 so we need to keep all transactions below this size.
    @staticmethod
    def transaction_size(signers: typing.Sequence[Keypair], instructions: typing.Sequence[TransactionInstruction]) -> int:
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

    def execute(self, context: Context, on_exception_continue: bool = False) -> typing.Sequence[str]:
        chunks: typing.Sequence[typing.Sequence[TransactionInstruction]
                                ] = _split_instructions_into_chunks(context, self.signers, self.instructions)

        if len(chunks) == 1 and len(chunks[0]) == 0:
            self.logger.info("No instructions to run.")
            return []

        if len(chunks) > 1:
            self.logger.info(f"Running instructions in {len(chunks)} transactions.")

        results: typing.List[str] = []
        for index, chunk in enumerate(chunks):
            transaction = Transaction()
            transaction.instructions.extend(chunk)
            try:
                response = context.client.send_transaction(transaction, *self.signers)
                results += [response]
            except Exception as exception:
                starts_at = sum(len(ch) for ch in chunks[0:index])
                if on_exception_continue:
                    self.logger.error(f"""[{context.name}] Error executing chunk {index} (instructions {starts_at} to {starts_at + len(chunk)}) of CombinableInstruction.
{exception}""")
                else:
                    raise exception

        return results

    def __str__(self) -> str:
        report: typing.List[str] = []
        for index, signer in enumerate(self.signers):
            report += [f"Signer[{index}]: {signer.public_key}"]

        instruction_reporter: InstructionReporter = InstructionReporter()
        for instruction in self.instructions:
            report += [instruction_reporter.report(instruction)]

        return "\n".join(report)

    def __repr__(self) -> str:
        return f"{self}"
