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

from .tokenvalue import TokenValue


# # 🥭 OwnedTokenValue class
#
# Ties an owner and `TokenValue` together. This is useful in the `TransactionScout`, where
# token mints and values are given separate from the owner `PublicKey` - we can package them
# together in this `OwnedTokenValue` class.

class OwnedTokenValue:
    def __init__(self, owner: PublicKey, token_value: TokenValue):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.owner = owner
        self.token_value = token_value

    @staticmethod
    def find_by_owner(values: typing.Sequence["OwnedTokenValue"], owner: PublicKey) -> "OwnedTokenValue":
        found = [value for value in values if value.owner == owner]
        if len(found) == 0:
            raise Exception(f"Owner '{owner}' not found in: {values}")

        if len(found) > 1:
            raise Exception(f"Owner '{owner}' matched multiple tokens in: {values}")

        return found[0]

    @staticmethod
    def changes(before: typing.Sequence["OwnedTokenValue"], after: typing.Sequence["OwnedTokenValue"]) -> typing.Sequence["OwnedTokenValue"]:
        changes: typing.List[OwnedTokenValue] = []
        for before_value in before:
            after_value = OwnedTokenValue.find_by_owner(after, before_value.owner)
            token_value = TokenValue(before_value.token_value.token,
                                     after_value.token_value.value - before_value.token_value.value)
            result = OwnedTokenValue(before_value.owner, token_value)
            changes += [result]

        return changes

    def __str__(self) -> str:
        return f"[{self.owner}]: {self.token_value}"

    def __repr__(self) -> str:
        return f"{self}"
