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
from solana.utils import shortvec_encoding as shortvec

from .context import Context
from .instructionreporter import InstructionReporter
from .wallet import Wallet

_MAXIMUM_TRANSACTION_LENGTH = 1280 - 40 - 8
_PUBKEY_LENGTH = 32
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
    # A toggle to run both checks to ensure our calculations are accurate.
    __check_transaction_size_with_pyserum = False

    def __init__(self, signers: typing.Sequence[Keypair], instructions: typing.Sequence[TransactionInstruction]) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
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

    # This is the expensive - but always accurate - way of calculating the size of a transaction.
    @staticmethod
    def _transaction_size_from_pyserum(signers: typing.Sequence[Keypair], instructions: typing.Sequence[TransactionInstruction]) -> int:
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

    # This is the quicker way - just add up the sizes ourselves. It's not trivial though.

    @staticmethod
    def _calculate_transaction_size(signers: typing.Sequence[Keypair], instructions: typing.Sequence[TransactionInstruction]) -> int:
        # Solana transactions have a deterministic size, but calculating it is a bit tricky.
        #
        # The transaction consists of:
        # * Message header
        # * count of number of instruction parcels
        # * 1 instruction parcel per instruction
        #
        # We're mostly interested in the number of distinct public keys used, rather than just the total number of public keys used
        # All distinct keys are passed in the message header, and 1-byte indexes are used in the instructions. That makes it all
        # a bit more compact.
        #
        # `shortvec` here is a compact representation of an integer that may take multiple bytes but only as many as it needs. What
        # we're interest in here is the count of the number of bytes the `shortvec` takes. It's normally 1, sometimes 2, but could be
        # any number.
        #
        # A public key is 32 bytes.
        #
        # A signature is 64 bytes.
        #
        # Message header is:
        # * 1 byte for number of signatures
        # * 1 byte for number of signed accounts
        # * 1 byte for number of unsigned accounts
        # * 32 bytes for recent blockhash
        # * (variable) shortvec length for number of distinct public keys
        # * (variable) 32 bytes * number  of distinct public keys
        #
        # This gives us a header size of:
        # 35 + (shortvec-length of distinct public keys) + (32 * number of distinct public keys)
        #
        # The count of number of instruction parcels is a shortvec length of the number of instructions
        #
        # Each instruction is:
        # * 1 byte for the program ID index
        # * (variable) shortvec length of the number of public keys
        # * (variable) 1 byte for the index of each account public key
        # * (variable) shortvec length of the data
        # * (variable) length of the data
        #
        # This gives us an instruction size of:
        # 1 + (shortvec-length of number of keys) + (number of keys) + (shortvec-length of the data) + (length of the data)
        #
        # This is signed, so the length is then:
        # * Message header size
        # * + each instruction size
        # * + shortvec-length of the number of signers
        # * + (number of signers * 64 bytes)
        #
        def shortvec_length(value: int) -> int:
            return len(shortvec.encode_length(value))

        program_ids = {instruction.program_id.to_base58() for instruction in instructions}
        meta_pubkeys = {meta.pubkey.to_base58() for instruction in instructions for meta in instruction.keys}
        distinct_publickeys = set.union(program_ids, meta_pubkeys, {
                                        signer.public_key.to_base58() for signer in signers})
        num_distinct_publickeys = len(distinct_publickeys)

        # 35 + (shortvec-length of distinct public keys) + (32 * number of distinct public keys)
        header_size = 35 + shortvec_length(num_distinct_publickeys) + (num_distinct_publickeys * _PUBKEY_LENGTH)

        instruction_count_length = shortvec_length(len(instructions))

        instructions_size = 0
        for inst in instructions:
            # 1 + (shortvec-length of number of keys) + (number of keys) + (shortvec-length of the data) + (length of the data)
            instructions_size += 1 + shortvec_length(len(inst.keys)) + len(inst.keys) + \
                shortvec_length(len(inst.data)) + len(inst.data)

        # Signatures
        signatures_size = 1 + (len(signers) * _SIGNATURE_LENGTH)

        # We can now calculate the total transaction size
        calculated_transaction_size = header_size + instruction_count_length + instructions_size + signatures_size
        return calculated_transaction_size

    # Calculate the exact size of a transaction. There's an upper limit of 1232 so we need to keep
    # all transactions below this size.
    @staticmethod
    def transaction_size(signers: typing.Sequence[Keypair], instructions: typing.Sequence[TransactionInstruction]) -> int:
        calculated_transaction_size = CombinableInstructions._calculate_transaction_size(signers, instructions)
        if CombinableInstructions.__check_transaction_size_with_pyserum:
            pyserum_transaction_size = CombinableInstructions._transaction_size_from_pyserum(signers, instructions)
            discrepancy = pyserum_transaction_size - calculated_transaction_size
            if discrepancy == 0:
                logging.debug(
                    f"txszcalc Calculated: {calculated_transaction_size}, Should be: {pyserum_transaction_size}, No Discrepancy!")
            else:
                logging.error(
                    f"txszcalcerr Calculated: {calculated_transaction_size}, Should be: {pyserum_transaction_size}, Discrepancy: {discrepancy}")
                return pyserum_transaction_size

        return calculated_transaction_size

    def __add__(self, new_instruction_data: "CombinableInstructions") -> "CombinableInstructions":
        all_signers = [*self.signers, *new_instruction_data.signers]
        all_instructions = [*self.instructions, *new_instruction_data.instructions]
        return CombinableInstructions(signers=all_signers, instructions=all_instructions)

    def execute(self, context: Context, on_exception_continue: bool = False) -> typing.Sequence[str]:
        chunks: typing.Sequence[typing.Sequence[TransactionInstruction]
                                ] = _split_instructions_into_chunks(context, self.signers, self.instructions)

        if len(chunks) == 1 and len(chunks[0]) == 0:
            self._logger.info("No instructions to run.")
            return []

        if len(chunks) > 1:
            self._logger.info(f"Running instructions in {len(chunks)} transactions.")

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
                    self._logger.error(f"""[{context.name}] Error executing chunk {index} (instructions {starts_at} to {starts_at + len(chunk)}) of CombinableInstruction.
{exception}""")
                else:
                    raise exception

        return results

    async def execute_async(self, context: Context, on_exception_continue: bool = False) -> typing.Sequence[str]:
        return self.execute(context, on_exception_continue)

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
