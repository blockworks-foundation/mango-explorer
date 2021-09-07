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

import enum
import typing

from decimal import Decimal
from solana.publickey import PublicKey

from .constants import MangoConstants
from .market import Market
from .marketlookup import MarketLookup
from .perpmarket import PerpMarketStub
from .spotmarket import SpotMarketStub
from .token import Token


class IdsJsonMarketType(enum.Enum):
    PERP = enum.auto()
    SPOT = enum.auto()

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 IdsJsonMarketLookup class
#
# This class allows us to look up market data from our ids.json configuration file.
#


class IdsJsonMarketLookup(MarketLookup):
    def __init__(self, cluster_name: str) -> None:
        super().__init__()
        self.cluster_name: str = cluster_name

    @staticmethod
    def _from_dict(market_type: IdsJsonMarketType, mango_program_address: PublicKey, group_address: PublicKey, data: typing.Dict, tokens: typing.Sequence[Token], quote_symbol: str) -> Market:
        base_symbol = data["baseSymbol"]
        base = Token.find_by_symbol(tokens, base_symbol)
        quote = Token.find_by_symbol(tokens, quote_symbol)
        address = PublicKey(data["publicKey"])
        if market_type == IdsJsonMarketType.PERP:
            return PerpMarketStub(mango_program_address, address, base, quote, group_address)
        else:
            return SpotMarketStub(mango_program_address, address, base, quote, group_address)

    @staticmethod
    def _load_tokens(data: typing.Dict) -> typing.Sequence[Token]:
        tokens: typing.List[Token] = []
        for token_data in data:
            token = Token(token_data["symbol"], token_data["symbol"], PublicKey(
                token_data["mintKey"]), Decimal(token_data["decimals"]))
            tokens += [token]
        return tokens

    def find_by_symbol(self, symbol: str) -> typing.Optional[Market]:
        check_spots = True
        check_perps = True
        symbol = symbol.upper()
        if symbol.startswith("SPOT:"):
            symbol = symbol.split(":", 1)[1]
            check_perps = False  # Skip perp markets because we're explicitly told it's a spot
        elif symbol.startswith("PERP:"):
            symbol = symbol.split(":", 1)[1]
            check_spots = False  # Skip spot markets because we're explicitly told it's a perp

        for group in MangoConstants["groups"]:
            if group["cluster"] == self.cluster_name:
                group_address: PublicKey = PublicKey(group["publicKey"])
                mango_program_address: PublicKey = PublicKey(group["mangoProgramId"])
                if check_perps:
                    for market_data in group["perpMarkets"]:
                        if market_data["name"].upper() == symbol.upper():
                            tokens = IdsJsonMarketLookup._load_tokens(group["tokens"])
                            return IdsJsonMarketLookup._from_dict(IdsJsonMarketType.PERP, mango_program_address, group_address, market_data, tokens, group["quoteSymbol"])
                if check_spots:
                    for market_data in group["spotMarkets"]:
                        if market_data["name"].upper() == symbol.upper():
                            tokens = IdsJsonMarketLookup._load_tokens(group["tokens"])
                            return IdsJsonMarketLookup._from_dict(IdsJsonMarketType.SPOT, mango_program_address, group_address, market_data, tokens, group["quoteSymbol"])
        return None

    def find_by_address(self, address: PublicKey) -> typing.Optional[Market]:
        for group in MangoConstants["groups"]:
            if group["cluster"] == self.cluster_name:
                group_address: PublicKey = PublicKey(group["publicKey"])
                mango_program_address: PublicKey = PublicKey(group["mangoProgramId"])
                for market_data in group["perpMarkets"]:
                    if market_data["key"] == str(address):
                        tokens = IdsJsonMarketLookup._load_tokens(group["tokens"])
                        return IdsJsonMarketLookup._from_dict(IdsJsonMarketType.PERP, mango_program_address, group_address, market_data, tokens, group["quoteSymbol"])
                for market_data in group["spotMarkets"]:
                    if market_data["key"] == str(address):
                        tokens = IdsJsonMarketLookup._load_tokens(group["tokens"])
                        return IdsJsonMarketLookup._from_dict(IdsJsonMarketType.SPOT, mango_program_address, group_address, market_data, tokens, group["quoteSymbol"])
        return None

    def all_markets(self) -> typing.Sequence[Market]:
        markets = []
        for group in MangoConstants["groups"]:
            if group["cluster"] == self.cluster_name:
                group_address: PublicKey = PublicKey(group["publicKey"])
                mango_program_address: PublicKey = PublicKey(group["mangoProgramId"])
                for market_data in group["perpMarkets"]:
                    tokens = IdsJsonMarketLookup._load_tokens(group["tokens"])
                    market = IdsJsonMarketLookup._from_dict(
                        IdsJsonMarketType.PERP, mango_program_address, group_address, market_data, tokens, group["quoteSymbol"])
                    markets = [market]
                for market_data in group["spotMarkets"]:
                    tokens = IdsJsonMarketLookup._load_tokens(group["tokens"])
                    market = IdsJsonMarketLookup._from_dict(
                        IdsJsonMarketType.SPOT, mango_program_address, group_address, market_data, tokens, group["quoteSymbol"])
                    markets = [market]

        return markets
