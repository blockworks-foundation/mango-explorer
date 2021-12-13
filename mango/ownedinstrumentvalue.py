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

from solana.publickey import PublicKey

from .instrumentvalue import InstrumentValue


# # 🥭 OwnedInstrumentValue class
#
# Ties an owner and `InstrumentValue` together. This is useful in the `TransactionScout`, where
# token mints and values are given separate from the owner `PublicKey` - we can package them
# together in this `OwnedInstrumentValue` class.

class OwnedInstrumentValue:
    def __init__(self, owner: PublicKey, token_value: InstrumentValue) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.owner = owner
        self.token_value = token_value

    @staticmethod
    def find_by_owner(values: typing.Sequence["OwnedInstrumentValue"], owner: PublicKey) -> "OwnedInstrumentValue":
        found = [value for value in values if value.owner == owner]
        if len(found) == 0:
            raise Exception(f"Owner '{owner}' not found in: {values}")

        if len(found) > 1:
            raise Exception(f"Owner '{owner}' matched multiple tokens in: {values}")

        return found[0]

    @staticmethod
    def changes(before: typing.Sequence["OwnedInstrumentValue"], after: typing.Sequence["OwnedInstrumentValue"]) -> typing.Sequence["OwnedInstrumentValue"]:
        changes: typing.List[OwnedInstrumentValue] = []
        for before_value in before:
            after_value = OwnedInstrumentValue.find_by_owner(after, before_value.owner)
            token_value = InstrumentValue(before_value.token_value.token,
                                          after_value.token_value.value - before_value.token_value.value)
            result = OwnedInstrumentValue(before_value.owner, token_value)
            changes += [result]

        return changes

    def __str__(self) -> str:
        return f"« OwnedInstrumentValue [{self.owner}]: {self.token_value} »"

    def __repr__(self) -> str:
        return f"{self}"
