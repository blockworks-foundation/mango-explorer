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


import typing

from pyserum._layouts.instructions import InstructionType as SerumInstructionType
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction

from .instructiontype import InstructionType
from .layouts import layouts
from .mangoinstruction import MangoInstruction


# # 🥭 InstructionReporter class
#
# The `InstructionReporter` class tries to load and present a decent readable interpretation of a Solana
# instruction.
#
class InstructionReporter:
    def matches(self, instruction: TransactionInstruction) -> bool:
        return True

    def report(self, instruction: TransactionInstruction) -> str:
        report: typing.List[str] = []
        for index, key in enumerate(instruction.keys):
            report += [f"Key[{index}]: {key.pubkey} {key.is_signer: <5} {key.is_writable: <5}"]
        report += [f"Program ID: {instruction.program_id}"]
        report += ["Data: " + "".join("{:02x}".format(x) for x in instruction.data)]
        return "\n".join(report)


# # 🥭 SerumInstructionReporter class
#
# The `SerumInstructionParser` class knows a bit more about Serum instructions.
#
class SerumInstructionReporter(InstructionReporter):
    def __init__(self, dex_program_id: PublicKey):
        self.dex_program_id: PublicKey = dex_program_id

    def matches(self, instruction: TransactionInstruction) -> bool:
        return instruction.program_id == self.dex_program_id

    def report(self, instruction: TransactionInstruction) -> str:
        initial = layouts.SERUM_INSTRUCTION_VARIANT_FINDER.parse(instruction.data)
        instruction_type = SerumInstructionType(initial.variant)
        return f"« Serum Instruction: {instruction_type.name}: " + "".join("{:02x}".format(x) for x in instruction.data) + "»"


# # 🥭 MangoInstructionReporter class
#
# The `MangoInstructionReporter` class knows a bit more about Mango instructions.
#
class MangoInstructionReporter(InstructionReporter):
    def __init__(self, program_id: PublicKey):
        self.program_id: PublicKey = program_id

    def matches(self, instruction: TransactionInstruction) -> bool:
        return instruction.program_id == self.program_id

    def report(self, instruction: TransactionInstruction) -> str:
        initial = layouts.MANGO_INSTRUCTION_VARIANT_FINDER.parse(instruction.data)
        parser = layouts.InstructionParsersByVariant[initial.variant]
        if parser is None:
            raise Exception(
                f"Could not find instruction parser for variant {initial.variant} / {InstructionType(initial.variant)}.")

        accounts: typing.List[PublicKey] = list(map(lambda meta: meta.pubkey, instruction.keys))
        parsed = parser.parse(instruction.data)
        instruction_type = InstructionType(int(parsed.variant))

        return str(MangoInstruction(instruction_type, parsed, accounts))


# # 🥭 CompoundInstructionReporter class
#
# The `CompoundInstructionReporter` class can combine multiple `InstructionReporter`s and pick the right one.
#
class CompoundInstructionReporter(InstructionReporter):
    def __init__(self, reporters: typing.Sequence[InstructionReporter]):
        self.reporters: typing.Sequence[InstructionReporter] = reporters

    def matches(self, instruction: TransactionInstruction) -> bool:
        for reporter in self.reporters:
            if reporter.matches(instruction):
                return True
        return False

    def report(self, instruction: TransactionInstruction) -> str:
        for reporter in self.reporters:
            if reporter.matches(instruction):
                return reporter.report(instruction)
        raise Exception(
            f"Could not find instruction reporter for instruction {instruction}.")

    @staticmethod
    def from_ids(program_id: PublicKey, dex_program_id: PublicKey) -> InstructionReporter:
        base: InstructionReporter = InstructionReporter()
        serum: InstructionReporter = SerumInstructionReporter(dex_program_id)
        mango: InstructionReporter = MangoInstructionReporter(program_id)
        return CompoundInstructionReporter([mango, serum, base])
