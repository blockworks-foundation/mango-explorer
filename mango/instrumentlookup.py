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
import json
import logging
import os.path
import typing

from decimal import Decimal
from solana.publickey import PublicKey

from .constants import DATA_PATH, MangoConstants
from .token import Instrument, Token


def _symbols_match(symbol1: str, symbol2: str) -> bool:
    return symbol1.upper() == symbol2.upper()


# # 🥭 InstrumentLookup class
#
# This class allows us to look up token symbols, names, decimals, and possibly mint addresses from Mango
# and Solana static data.
#
# It's usually easiest to access it via the `Context` as `context.instrument_lookup`.
#
class InstrumentLookup(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def find_by_symbol(self, symbol: str) -> typing.Optional[Instrument]:
        raise NotImplementedError("InstrumentLookup.find_by_symbol() is not implemented on the base type.")

    @abc.abstractmethod
    def find_by_mint(self, mint: PublicKey) -> typing.Optional[Instrument]:
        raise NotImplementedError("InstrumentLookup.find_by_mint() is not implemented on the base type.")

    def find_by_symbol_or_raise(self, symbol: str) -> Instrument:
        token = self.find_by_symbol(symbol)
        if token is None:
            raise Exception(f"Could not find token with symbol '{symbol}'.")

        return token

    def find_by_mint_or_raise(self, mint: PublicKey) -> Token:
        token = self.find_by_mint(mint)
        if token is None or not isinstance(token, Token):
            raise Exception(f"Could not find token with mint {mint}.")

        return token

    def __repr__(self) -> str:
        return f"{self}"

    def __str__(self) -> str:
        return """« InstrumentLookup »"""


# # 🥭 NullInstrumentLookup class
#
# This class is a simple stub `InstrumentLookup` that never returns a `Instrument`.
#
class NullInstrumentLookup(InstrumentLookup):
    def __init__(self) -> None:
        super().__init__()

    def find_by_symbol(self, symbol: str) -> typing.Optional[Instrument]:
        return None

    def find_by_mint(self, mint: PublicKey) -> typing.Optional[Instrument]:
        return None

    def __str__(self) -> str:
        return "« NullInstrumentLookup »"


# # 🥭 CompoundInstrumentLookup class
#
# This class allows multiple `InstrumentLookup` objects to be combined, returning the first valid lookup result
# found.
#
class CompoundInstrumentLookup(InstrumentLookup):
    def __init__(self, lookups: typing.Sequence[InstrumentLookup]) -> None:
        super().__init__()
        self.lookups: typing.Sequence[InstrumentLookup] = lookups

    def find_by_symbol(self, symbol: str) -> typing.Optional[Instrument]:
        for lookup in self.lookups:
            result = lookup.find_by_symbol(symbol)
            if result is not None:
                return result
        return None

    def find_by_mint(self, mint: PublicKey) -> typing.Optional[Instrument]:
        for lookup in self.lookups:
            result = lookup.find_by_mint(mint)
            if result is not None:
                return result
        return None

    def __str__(self) -> str:
        inner = "\n    ".join([f"{item}".replace("\n", "\n    ") for item in self.lookups])
        return f"""« CompoundInstrumentLookup
    {inner}
»"""


# # 🥭 NonSPLInstrumentLookup class
#
# This class allows us to look up non-SPL token data specifically from static data. This is useful for instruments
# that don't have an underlying SPL-token, such as ADA in ADA-PERP.
#
# You can load an `NonSPLInstrumentLookup` class by something like:
# ```
# with open("nonspl.instrumentlist.json") as json_file:
#     token_data = json.load(json_file)
#     token_lookup = NonSPLInstrumentLookup(token_data)
# ```
#
class NonSPLInstrumentLookup(InstrumentLookup):
    DefaultMainnetDataFilepath = os.path.join(DATA_PATH, "nonspl.instrumentlist.json")
    DefaultDevnetDataFilepath = os.path.join(DATA_PATH, "nonspl.instrumentlist.devnet.json")

    def __init__(self, filename: str, token_data: typing.Dict[str, typing.Any]) -> None:
        super().__init__()
        self.filename: str = filename
        self.token_data: typing.Dict[str, typing.Any] = token_data

    def find_by_symbol(self, symbol: str) -> typing.Optional[Instrument]:
        for token in self.token_data["tokens"]:
            if _symbols_match(token["symbol"], symbol):
                return Instrument(token["symbol"], token["name"], Decimal(token["decimals"]))

        return None

    def find_by_mint(self, mint: PublicKey) -> typing.Optional[Instrument]:
        return None

    @staticmethod
    def load(filename: str) -> "NonSPLInstrumentLookup":
        with open(filename, encoding="utf-8") as json_file:
            token_data = json.load(json_file)
            return NonSPLInstrumentLookup(filename, token_data)

    def __str__(self) -> str:
        return f"« NonSPLInstrumentLookup [{self.filename}] »"


# # 🥭 IdsJsonTokenLookup class
#
# This class allows us to look up token data from our ids.json configuration file.
#
class IdsJsonTokenLookup(InstrumentLookup):
    def __init__(self, cluster_name: str, group_name: str) -> None:
        super().__init__()
        self.cluster_name: str = cluster_name
        self.group_name: str = group_name

    def find_by_symbol(self, symbol: str) -> typing.Optional[Token]:
        for group in MangoConstants["groups"]:
            if group["cluster"] == self.cluster_name and group["name"] == self.group_name:
                for token in group["tokens"]:
                    if _symbols_match(token["symbol"], symbol):
                        return Token(token["symbol"], token["symbol"], Decimal(token["decimals"]), PublicKey(token["mintKey"]))
        return None

    def find_by_mint(self, mint: PublicKey) -> typing.Optional[Token]:
        mint_str = str(mint)
        for group in MangoConstants["groups"]:
            if group["cluster"] == self.cluster_name and group["name"] == self.group_name:
                for token in group["tokens"]:
                    if token["mintKey"] == mint_str:
                        return Token(token["symbol"], token["symbol"], Decimal(token["decimals"]), PublicKey(token["mintKey"]))
        return None

    def __str__(self) -> str:
        return f"« IdsJsonTokenLookup [{self.cluster_name}, {self.group_name}] »"


# # 🥭 SPLTokenLookup class
#
# This class allows us to look up token data specifically from Solana static data.
#
# The Solana static data is the [Solana token list](https://raw.githubusercontent.com/solana-labs/token-list/main/src/tokens/solana.tokenlist.json) provided by Serum.
#
# You can load an `SPLTokenLookup` class by something like:
# ```
# with open("solana.tokenlist.json") as json_file:
#     token_data = json.load(json_file)
#     token_lookup = SPLTokenLookup(token_data)
# ```
#
class SPLTokenLookup(InstrumentLookup):
    DefaultDataFilepath = os.path.join(DATA_PATH, "solana.tokenlist.json")

    def __init__(self, filename: str, token_data: typing.Dict[str, typing.Any]) -> None:
        super().__init__()
        self.filename: str = filename
        self.token_data: typing.Dict[str, typing.Any] = token_data

    def find_by_symbol(self, symbol: str) -> typing.Optional[Token]:
        for token in self.token_data["tokens"]:
            if _symbols_match(token["symbol"], symbol):
                return Token(token["symbol"], token["name"], Decimal(token["decimals"]), PublicKey(token["address"]))

        return None

    def find_by_mint(self, mint: PublicKey) -> typing.Optional[Token]:
        mint_string: str = str(mint)
        for token in self.token_data["tokens"]:
            if token["address"] == mint_string:
                return Token(token["symbol"], token["name"], Decimal(token["decimals"]), PublicKey(token["address"]))

        return None

    @staticmethod
    def load(filename: str) -> "SPLTokenLookup":
        with open(filename, encoding="utf-8") as json_file:
            token_data = json.load(json_file)
            return SPLTokenLookup(filename, token_data)

    def __str__(self) -> str:
        return f"« SPLTokenLookup [{self.filename}] »"
