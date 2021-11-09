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

from solana.publickey import PublicKey

from .constants import MangoConstants
from .instrumentlookup import InstrumentLookup
from .market import Market
from .marketlookup import MarketLookup
from .perpmarket import PerpMarketStub
from .spotmarket import SpotMarketStub
from .token import Instrument, Token


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
    def __init__(self, cluster_name: str, instrument_lookup: InstrumentLookup) -> None:
        super().__init__()
        self.cluster_name: str = cluster_name
        self.instrument_lookup: InstrumentLookup = instrument_lookup

    @staticmethod
    def _from_dict(market_type: IdsJsonMarketType, mango_program_address: PublicKey, group_address: PublicKey, data: typing.Dict[str, typing.Any], instrument_lookup: InstrumentLookup, quote_symbol: str) -> Market:
        base_symbol = data["baseSymbol"]
        base_instrument: typing.Optional[Instrument] = instrument_lookup.find_by_symbol(base_symbol)
        if base_instrument is None:
            raise Exception(f"Could not find base instrument with symbol '{base_symbol}'")
        quote_instrument: typing.Optional[Instrument] = instrument_lookup.find_by_symbol(quote_symbol)
        if quote_instrument is None:
            raise Exception(f"Could not find quote token with symbol '{quote_symbol}'")
        quote: Token = Token.ensure(quote_instrument)
        address = PublicKey(data["publicKey"])
        if market_type == IdsJsonMarketType.PERP:
            return PerpMarketStub(mango_program_address, address, base_instrument, quote, group_address)
        else:
            base: Token = Token.ensure(base_instrument)
            return SpotMarketStub(mango_program_address, address, base, quote, group_address)

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
                            return IdsJsonMarketLookup._from_dict(IdsJsonMarketType.PERP, mango_program_address, group_address, market_data, self.instrument_lookup, group["quoteSymbol"])
                if check_spots:
                    for market_data in group["spotMarkets"]:
                        if market_data["name"].upper() == symbol.upper():
                            return IdsJsonMarketLookup._from_dict(IdsJsonMarketType.SPOT, mango_program_address, group_address, market_data, self.instrument_lookup, group["quoteSymbol"])
        return None

    def find_by_address(self, address: PublicKey) -> typing.Optional[Market]:
        for group in MangoConstants["groups"]:
            if group["cluster"] == self.cluster_name:
                group_address: PublicKey = PublicKey(group["publicKey"])
                mango_program_address: PublicKey = PublicKey(group["mangoProgramId"])
                for market_data in group["perpMarkets"]:
                    if market_data["publicKey"] == str(address):
                        return IdsJsonMarketLookup._from_dict(IdsJsonMarketType.PERP, mango_program_address, group_address, market_data, self.instrument_lookup, group["quoteSymbol"])
                for market_data in group["spotMarkets"]:
                    if market_data["publicKey"] == str(address):
                        return IdsJsonMarketLookup._from_dict(IdsJsonMarketType.SPOT, mango_program_address, group_address, market_data, self.instrument_lookup, group["quoteSymbol"])
        return None

    def all_markets(self) -> typing.Sequence[Market]:
        markets = []
        for group in MangoConstants["groups"]:
            if group["cluster"] == self.cluster_name:
                group_address: PublicKey = PublicKey(group["publicKey"])
                mango_program_address: PublicKey = PublicKey(group["mangoProgramId"])
                for market_data in group["perpMarkets"]:
                    market = IdsJsonMarketLookup._from_dict(
                        IdsJsonMarketType.PERP, mango_program_address, group_address, market_data, self.instrument_lookup, group["quoteSymbol"])
                    markets = [market]
                for market_data in group["spotMarkets"]:
                    market = IdsJsonMarketLookup._from_dict(
                        IdsJsonMarketType.SPOT, mango_program_address, group_address, market_data, self.instrument_lookup, group["quoteSymbol"])
                    markets = [market]

        return markets
