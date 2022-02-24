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
import multiprocessing
import requests
import types
import typing

from decimal import Decimal
from rx.scheduler.threadpoolscheduler import ThreadPoolScheduler
from solana.publickey import PublicKey
from solana.rpc.commitment import Commitment

from .client import (
    BetterClient,
    ClusterUrlData,
    TransactionMonitor,
    NullTransactionMonitor,
)
from .constants import MangoConstants
from .idgenerator import IdGenerator, MonotonicIdGenerator
from .instructionreporter import InstructionReporter, CompoundInstructionReporter
from .instrumentlookup import InstrumentLookup
from .marketlookup import MarketLookup
from .text import indent_collection_as_str, indent_item_by
from .tokens import Instrument, Token


# # 🥭 Context class
#
# A `Context` object to manage Solana connection and Mango configuration.
#
class Context:
    def __init__(
        self,
        name: str,
        cluster_name: str,
        cluster_urls: typing.Sequence[ClusterUrlData],
        skip_preflight: bool,
        tpu_retransmissions: int,
        commitment: str,
        encoding: str,
        blockhash_cache_duration: int,
        http_request_timeout: float,
        stale_data_pauses_before_retry: typing.Sequence[float],
        mango_program_address: PublicKey,
        serum_program_address: PublicKey,
        group_name: str,
        group_address: PublicKey,
        gma_chunk_size: Decimal,
        gma_chunk_pause: Decimal,
        reflink: typing.Optional[PublicKey],
        instrument_lookup: InstrumentLookup,
        market_lookup: MarketLookup,
        transaction_monitor: TransactionMonitor = NullTransactionMonitor(),
    ) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.name: str = name
        instruction_reporter: InstructionReporter = (
            CompoundInstructionReporter.from_addresses(
                mango_program_address, serum_program_address
            )
        )
        self.client: BetterClient = BetterClient.from_configuration(
            name,
            cluster_name,
            cluster_urls,
            Commitment(commitment),
            skip_preflight,
            tpu_retransmissions,
            encoding,
            blockhash_cache_duration,
            http_request_timeout,
            stale_data_pauses_before_retry,
            instruction_reporter,
            transaction_monitor,
        )
        self.mango_program_address: PublicKey = mango_program_address
        self.serum_program_address: PublicKey = serum_program_address
        self.group_name: str = group_name
        self.group_address: PublicKey = group_address
        self.gma_chunk_size: Decimal = gma_chunk_size
        self.gma_chunk_pause: Decimal = gma_chunk_pause
        self.reflink: typing.Optional[PublicKey] = reflink
        self.instrument_lookup: InstrumentLookup = instrument_lookup
        self.market_lookup: MarketLookup = market_lookup

        self.ping_interval: int = 10

        self.__id_generator: IdGenerator = MonotonicIdGenerator()

        # kangda said in Discord: https://discord.com/channels/791995070613159966/836239696467591186/847816026245693451
        # "I think you are better off doing 4,8,16,20,30"
        self.retry_pauses: typing.Sequence[Decimal] = [
            Decimal(4),
            Decimal(8),
            Decimal(16),
            Decimal(20),
            Decimal(30),
        ]

    def __enter__(self) -> "Context":
        return self

    def __exit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_value: typing.Optional[BaseException],
        traceback: typing.Optional[types.TracebackType],
    ) -> None:
        self.dispose()

    def dispose(self) -> None:
        self.client.dispose()

    def create_thread_pool_scheduler(self) -> ThreadPoolScheduler:
        return ThreadPoolScheduler(multiprocessing.cpu_count())

    def generate_client_id(self) -> int:
        return self.__id_generator.generate_id()

    def lookup_group_name(self, group_address: PublicKey) -> str:
        group_address_str = str(group_address)
        for group in MangoConstants["groups"]:
            if (
                group["cluster"] == self.client.cluster_name
                and group["publicKey"] == group_address_str
            ):
                return str(group["name"])

        return "« Unknown Group »"

    def instrument(self, symbol: str) -> Instrument:
        instrument = self.instrument_lookup.find_by_symbol(symbol)
        if instrument is None:
            raise Exception(f"Could not find instrument with symbol '{symbol}'.")
        return instrument

    def token(self, symbol: str) -> Token:
        instrument = self.instrument_lookup.find_by_symbol(symbol)
        if instrument is None:
            raise Exception(f"Could not find token with symbol '{symbol}'.")
        return Token.ensure(instrument)

    def fetch_stats(self, url_suffix: str) -> typing.Sequence[typing.Any]:
        stats_url = f"https://mango-stats-v3.herokuapp.com/{url_suffix}"
        stats_response = requests.get(stats_url)
        return typing.cast(typing.Sequence[typing.Any], stats_response.json())

    def __str__(self) -> str:
        cluster_urls: str = indent_item_by(
            indent_collection_as_str(self.client.cluster_urls)
        )
        return f"""« Context '{self.name}':
    Cluster Name: {self.client.cluster_name}
    Cluster URLs:
        {cluster_urls}
    Group Name: {self.group_name}
    Group Address: {self.group_address}
    Mango Program Address: {self.mango_program_address}
    Serum Program Address: {self.serum_program_address}
»"""

    def __repr__(self) -> str:
        return f"{self}"
