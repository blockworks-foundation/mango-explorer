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

import argparse
import logging
import os
import typing

from decimal import Decimal
from solana.publickey import PublicKey
from solana.rpc.commitment import Commitment, Finalized

from .client import (
    AbstractSlotHolder,
    CheckingSlotHolder,
    ClusterUrlData,
    NullSlotHolder,
    TransactionMonitor,
    NullTransactionMonitor,
)
from .constants import MangoConstants
from .context import Context
from .idsjsonmarketlookup import IdsJsonMarketLookup
from .instrumentlookup import (
    InstrumentLookup,
    CompoundInstrumentLookup,
    IdsJsonTokenLookup,
    NonSPLInstrumentLookup,
    SPLTokenLookup,
)
from .marketlookup import CompoundMarketLookup, MarketLookup
from .serummarketlookup import SerumMarketLookup
from .transactionmonitoring import (
    DequeTransactionStatusCollector,
    WebSocketTransactionMonitor,
)


# # 🥭 ContextBuilder
#
# ## Environment Variables
#
# It's possible to override the values in the `Context` variables provided. This can be easier than creating
# the `Context` in code or introducing dependencies and configuration.
#
# The following environment variables are read:
# * NAME
# * CLUSTER
# * CLUSTER_URL
# * GROUP_NAME
# * GROUP_ADDRESS
# * MANGO_PROGRAM_ADDRESS
# * SERUM_PROGRAM_ADDRESS
# * MANGO_REFLINK_ADDRESS


# # 🥭 ContextBuilder class
#
# A `ContextBuilder` class to allow building `Context` objects without introducing circular dependencies.
#
class ContextBuilder:

    # Utility class for parsing cluster-url command line parameter
    #
    class ParseClusterUrls(argparse.Action):
        cluster_urls: typing.List[ClusterUrlData] = []

        def __call__(
            self,
            parser: argparse.ArgumentParser,
            namespace: object,
            values: typing.Any,
            option_string: typing.Optional[str] = None,
        ) -> None:
            if values:
                if len(values) == 1:
                    self.cluster_urls.append(ClusterUrlData(rpc=values[0]))
                elif len(values) == 2:
                    self.cluster_urls.append(
                        ClusterUrlData(rpc=values[0], ws=values[1])
                    )
                else:
                    raise parser.error(
                        "Argument --cluster-url permits maximal two parameters. The first one configures HTTP connection url, the second one "
                        "configures the WS connection url. Example: --cluster-url https://localhost:8181 wss://localhost:8282"
                    )
                setattr(namespace, self.dest, self.cluster_urls)

    # Configuring a `Context` is a common operation for command-line programs and can involve a
    # lot of duplicate code.
    #
    # This function centralises some of it to ensure consistency and readability.
    #
    @staticmethod
    def add_command_line_parameters(
        parser: argparse.ArgumentParser, monitor_transactions_default: bool = False
    ) -> None:
        parser.add_argument(
            "--name",
            type=str,
            default="Mango Explorer",
            help="Name of the program (used in reports and alerts)",
        )
        parser.add_argument(
            "--cluster-name", type=str, default=None, help="Solana RPC cluster name"
        )
        parser.add_argument(
            "--cluster-url",
            nargs="*",
            type=str,
            action=ContextBuilder.ParseClusterUrls,
            default=[],
            help="Solana RPC cluster URL (can be specified multiple times to provide failover when one errors; optional second parameter value defines websocket connection)",
        )
        parser.add_argument(
            "--group-name", type=str, default=None, help="Mango group name"
        )
        parser.add_argument(
            "--group-address", type=PublicKey, default=None, help="Mango group address"
        )
        parser.add_argument(
            "--mango-program-address",
            type=PublicKey,
            default=None,
            help="Mango program address",
        )
        parser.add_argument(
            "--serum-program-address",
            type=PublicKey,
            default=None,
            help="Serum program address",
        )
        parser.add_argument(
            "--skip-preflight",
            default=False,
            action="store_true",
            help="Skip pre-flight checks",
        )
        parser.add_argument(
            "--tpu-retransmissions",
            default=-1,
            type=int,
            help="Number of attempts the RPC node runs to deliver a transaction to TPU (default -1 means redelivering until success or recent blockhash expires)",
        )
        parser.add_argument(
            "--commitment",
            type=str,
            default=None,
            help="Commitment to use when sending transactions (can be 'finalized', 'confirmed' or 'processed')",
        )
        parser.add_argument(
            "--encoding",
            type=str,
            default=None,
            help="Encoding to request when receiving data from Solana (options are 'base58' (slow), 'base64', 'base64+zstd', or 'jsonParsed')",
        )
        parser.add_argument(
            "--blockhash-cache-duration",
            type=int,
            help="How long (in seconds) to cache 'recent' blockhashes",
        )
        parser.add_argument(
            "--http-request-timeout",
            type=float,
            default=20,
            help="What is the timeout for HTTP requests to when calling to RPC nodes (in seconds), -1 means no timeout",
        )
        parser.add_argument(
            "--stale-data-pause-before-retry",
            type=Decimal,
            help="How long (in seconds, e.g. 0.1) to pause after retrieving stale data before retrying",
        )
        parser.add_argument(
            "--stale-data-maximum-retries",
            type=int,
            default=0,
            help="How many times to retry fetching data after being given stale data before giving up",
        )
        parser.add_argument(
            "--monitor-transactions",
            default=monitor_transactions_default,
            action="store_true",
            help="Watch transactions and log their results",
        )
        parser.add_argument(
            "--monitor-transactions-commitment",
            type=Commitment,
            default=Finalized,
            help="Monitor transactions until they reach this commitment level",
        )
        parser.add_argument(
            "--monitor-transactions-timeout",
            type=float,
            default=90,
            help="Time after which to assume a transaction will not reach the specified commitment level",
        )
        parser.add_argument(
            "--gma-chunk-size",
            type=Decimal,
            default=None,
            help="Maximum number of addresses to send in a single call to getMultipleAccounts()",
        )
        parser.add_argument(
            "--gma-chunk-pause",
            type=Decimal,
            default=None,
            help="Number of seconds to pause between successive getMultipleAccounts() calls to avoid rate limiting",
        )
        parser.add_argument(
            "--reflink", type=PublicKey, default=None, help="Referral public key"
        )

    # This function is the converse of `add_command_line_parameters()` - it takes
    # an argument of parsed command-line parameters and expects to see the ones it added
    # to that collection in the `add_command_line_parameters()` call.
    #
    # It then uses those parameters to create a properly-configured `Context` object.
    #
    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> Context:
        name: typing.Optional[str] = args.name
        cluster_name: typing.Optional[str] = args.cluster_name
        cluster_urls: typing.Optional[
            typing.Sequence[ClusterUrlData]
        ] = args.cluster_url
        group_name: typing.Optional[str] = args.group_name
        group_address: typing.Optional[PublicKey] = args.group_address
        mango_program_address: typing.Optional[PublicKey] = args.mango_program_address
        serum_program_address: typing.Optional[PublicKey] = args.serum_program_address
        skip_preflight: bool = bool(args.skip_preflight)
        tpu_retransmissions: int = int(args.tpu_retransmissions)
        commitment: typing.Optional[str] = args.commitment
        encoding: typing.Optional[str] = args.encoding
        blockhash_cache_duration: typing.Optional[int] = args.blockhash_cache_duration
        http_request_timeout: typing.Optional[float] = args.http_request_timeout
        stale_data_pause_before_retry: typing.Optional[
            Decimal
        ] = args.stale_data_pause_before_retry
        stale_data_maximum_retries: typing.Optional[
            int
        ] = args.stale_data_maximum_retries
        gma_chunk_size: typing.Optional[Decimal] = args.gma_chunk_size
        gma_chunk_pause: typing.Optional[Decimal] = args.gma_chunk_pause
        reflink: typing.Optional[PublicKey] = args.reflink
        monitor_transactions: bool = bool(args.monitor_transactions)
        monitor_transactions_commitment: typing.Optional[
            Commitment
        ] = args.monitor_transactions_commitment
        monitor_transactions_timeout: typing.Optional[
            float
        ] = args.monitor_transactions_timeout

        # Do this here so build() only ever has to handle the sequence of retry times. (It gets messy
        # passing around the sequnce *plus* the data to reconstruct it for build().)
        actual_stale_data_pauses_before_retry: typing.Sequence[float]
        actual_slot_holder: AbstractSlotHolder
        if stale_data_maximum_retries == 0:
            # Stale data checking is disabled
            actual_stale_data_pauses_before_retry = []
            actual_slot_holder = NullSlotHolder()
        else:
            retries: int = stale_data_maximum_retries or 10
            pause: Decimal = stale_data_pause_before_retry or Decimal("0.1")
            actual_stale_data_pauses_before_retry = [float(pause)] * retries
            actual_slot_holder = CheckingSlotHolder()

        context: Context = ContextBuilder.build(
            name,
            cluster_name,
            cluster_urls,
            skip_preflight,
            tpu_retransmissions,
            commitment,
            encoding,
            blockhash_cache_duration,
            http_request_timeout,
            actual_stale_data_pauses_before_retry,
            group_name,
            group_address,
            mango_program_address,
            serum_program_address,
            gma_chunk_size,
            gma_chunk_pause,
            reflink,
            monitor_transactions,
            monitor_transactions_commitment,
            monitor_transactions_timeout,
            actual_slot_holder,
        )

        logging.debug(f"{context}")

        return context

    @staticmethod
    def default() -> Context:
        return ContextBuilder.build()

    @staticmethod
    def from_group_name(context: Context, group_name: str) -> Context:
        return ContextBuilder.build(
            context.name,
            context.client.cluster_name,
            context.client.cluster_urls,
            context.client.skip_preflight,
            context.client.tpu_retransmissions,
            context.client.commitment,
            context.client.encoding,
            context.client.blockhash_cache_duration,
            None,
            context.client.stale_data_pauses_before_retry,
            group_name,
            None,
            None,
            None,
            context.gma_chunk_size,
            context.gma_chunk_pause,
            context.reflink,
            not isinstance(context.client.transaction_monitor, NullTransactionMonitor),
            context.client.transaction_monitor.commitment,
            context.client.transaction_monitor.transaction_timeout,
            context.client.transaction_monitor.slot_holder,
        )

    @staticmethod
    def force_to_cluster(context: Context, cluster_name: str) -> Context:
        return ContextBuilder.build(
            context.name,
            cluster_name,
            None,  # Can't use parameter cluster URLs if we're switching network
            context.client.skip_preflight,
            context.client.tpu_retransmissions,
            context.client.commitment,
            context.client.encoding,
            context.client.blockhash_cache_duration,
            context.client.rpc_caller.all_providers[0].http_request_timeout,
            context.client.stale_data_pauses_before_retry,
            None,  # Use new cluster's default Group name
            None,  # Use new cluster's default Group address
            None,  # Use new cluster's default Program address
            None,  # Use new cluster's default Serum address
            context.gma_chunk_size,
            context.gma_chunk_pause,
            context.reflink,
            False,  # Don't try to watch transactions on a switched Context
            None,
            None,
            NullSlotHolder(),
        )

    @staticmethod
    def build(
        name: typing.Optional[str] = None,
        cluster_name: typing.Optional[str] = None,
        cluster_urls: typing.Optional[typing.Sequence[ClusterUrlData]] = None,
        skip_preflight: bool = False,
        tpu_retransmissions: int = -1,
        commitment: typing.Optional[str] = None,
        encoding: typing.Optional[str] = None,
        blockhash_cache_duration: typing.Optional[int] = None,
        http_request_timeout: typing.Optional[float] = None,
        stale_data_pauses_before_retry: typing.Optional[typing.Sequence[float]] = None,
        group_name: typing.Optional[str] = None,
        group_address: typing.Optional[PublicKey] = None,
        program_address: typing.Optional[PublicKey] = None,
        serum_program_address: typing.Optional[PublicKey] = None,
        gma_chunk_size: typing.Optional[Decimal] = None,
        gma_chunk_pause: typing.Optional[Decimal] = None,
        reflink: typing.Optional[PublicKey] = None,
        monitor_transactions: typing.Optional[bool] = None,
        monitor_transactions_commitment: typing.Optional[Commitment] = None,
        monitor_transactions_timeout: typing.Optional[float] = None,
        slot_holder: typing.Optional[AbstractSlotHolder] = None,
    ) -> "Context":
        def __public_key_or_none(
            address: typing.Optional[str],
        ) -> typing.Optional[PublicKey]:
            if address is not None and address != "":
                return PublicKey(address)
            return None

        # The first group is only used to determine the default cluster if it is not otherwise specified.
        first_group_data = MangoConstants["groups"][0]
        actual_name: str = name or os.environ.get("NAME") or "Mango Explorer"
        actual_cluster: str = (
            cluster_name
            or os.environ.get("CLUSTER_NAME")
            or first_group_data["cluster"]
        )

        # Now that we have the actual cluster name, taking environment variables and defaults into account,
        # we can decide what we want as the default group.
        for group_data in MangoConstants["groups"]:
            if group_data["cluster"] == actual_cluster:
                default_group_data = group_data
                break

        actual_commitment: str = commitment or "processed"
        actual_encoding: str = encoding or "base64"
        actual_blockhash_cache_duration: int = blockhash_cache_duration or 0
        actual_stale_data_pauses_before_retry: typing.Sequence[float] = (
            stale_data_pauses_before_retry or []
        )
        actual_http_request_timeout: float = http_request_timeout or -1
        actual_tpu_retransmissions: int = int(tpu_retransmissions)

        actual_cluster_urls: typing.Optional[
            typing.Sequence[ClusterUrlData]
        ] = cluster_urls
        if actual_cluster_urls is None or len(actual_cluster_urls) == 0:
            cluster_url_from_environment: typing.Optional[str] = os.environ.get(
                "CLUSTER_URL"
            )
            if (
                cluster_url_from_environment is not None
                and cluster_url_from_environment != ""
            ):
                actual_cluster_urls = [ClusterUrlData(rpc=cluster_url_from_environment)]
            else:
                actual_cluster_urls = [
                    ClusterUrlData(rpc=MangoConstants["cluster_urls"][actual_cluster])
                ]

        actual_skip_preflight: bool = skip_preflight
        actual_group_name: str = (
            group_name or os.environ.get("GROUP_NAME") or default_group_data["name"]
        )

        found_group_data: typing.Any = None
        for group in MangoConstants["groups"]:
            if (
                group["cluster"] == actual_cluster
                and group["name"].upper() == actual_group_name.upper()
            ):
                found_group_data = group

        if found_group_data is None:
            raise Exception(
                f"Could not find group named '{actual_group_name}' in cluster '{actual_cluster}'."
            )

        actual_group_address: PublicKey = (
            group_address
            or __public_key_or_none(os.environ.get("GROUP_ADDRESS"))
            or PublicKey(found_group_data["publicKey"])
        )
        actual_program_address: PublicKey = (
            program_address
            or __public_key_or_none(os.environ.get("MANGO_PROGRAM_ADDRESS"))
            or PublicKey(found_group_data["mangoProgramId"])
        )
        actual_serum_program_address: PublicKey = (
            serum_program_address
            or __public_key_or_none(os.environ.get("SERUM_PROGRAM_ADDRESS"))
            or PublicKey(found_group_data["serumProgramId"])
        )

        actual_gma_chunk_size: Decimal = gma_chunk_size or Decimal(100)
        actual_gma_chunk_pause: Decimal = gma_chunk_pause or Decimal(0)

        actual_reflink: typing.Optional[PublicKey] = reflink or __public_key_or_none(
            os.environ.get("MANGO_REFLINK_ADDRESS")
        )

        ids_json_token_lookup: InstrumentLookup = IdsJsonTokenLookup(
            actual_cluster, actual_group_name
        )
        instrument_lookup: InstrumentLookup = ids_json_token_lookup
        if actual_cluster == "mainnet":
            # 'Overrides' are for problematic situations.
            #
            # We want to be able to use the community-owned SPL Token Registry JSON file. It holds details
            # of most tokens and allows our Serum code to work with any of them and their markets.
            #
            # The problems come when they decide to rename symbols, like they did with "ETH".
            #
            # Mango uses "ETH" with a mint 2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk and for a long time
            # the SPL JSON file also used "ETH" with a mint of 2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk.
            #
            # Then the SPL JSON file was updated and the mint 2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk now
            # has the symbol 'soETH' for 'Wrapped Ethereum (Sollet)', and "ETH" is now 'Wrapped Ether (Wormhole)'
            # with a mint of 7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs.
            #
            # 'Overrides' allows us to put the details we expect for 'ETH' into our loader, ahead of the SPL
            # JSON, so that our code and users can continue to use, for example, ETH/USDT, as they expect.
            mainnet_overrides_token_lookup: InstrumentLookup = SPLTokenLookup.load(
                SPLTokenLookup.OverridesDataFilepath
            )
            mainnet_spl_token_lookup: InstrumentLookup = SPLTokenLookup.load(
                SPLTokenLookup.DefaultDataFilepath
            )
            mainnet_non_spl_instrument_lookup: InstrumentLookup = (
                NonSPLInstrumentLookup.load(
                    NonSPLInstrumentLookup.DefaultMainnetDataFilepath
                )
            )
            instrument_lookup = CompoundInstrumentLookup(
                [
                    ids_json_token_lookup,
                    mainnet_overrides_token_lookup,
                    mainnet_non_spl_instrument_lookup,
                    mainnet_spl_token_lookup,
                ]
            )
        elif actual_cluster == "devnet":
            devnet_overrides_token_lookup: InstrumentLookup = SPLTokenLookup.load(
                SPLTokenLookup.DevnetOverridesDataFilepath
            )
            devnet_spl_token_lookup: InstrumentLookup = SPLTokenLookup.load(
                SPLTokenLookup.DevnetDataFilepath
            )
            devnet_non_spl_instrument_lookup: InstrumentLookup = (
                NonSPLInstrumentLookup.load(
                    NonSPLInstrumentLookup.DefaultDevnetDataFilepath
                )
            )
            instrument_lookup = CompoundInstrumentLookup(
                [
                    ids_json_token_lookup,
                    devnet_overrides_token_lookup,
                    devnet_non_spl_instrument_lookup,
                    devnet_spl_token_lookup,
                ]
            )

        ids_json_market_lookup: MarketLookup = IdsJsonMarketLookup(
            actual_cluster, instrument_lookup
        )
        all_market_lookup = ids_json_market_lookup
        if actual_cluster == "mainnet":
            mainnet_overrides_serum_market_lookup: SerumMarketLookup = (
                SerumMarketLookup.load(
                    actual_serum_program_address, SPLTokenLookup.OverridesDataFilepath
                )
            )
            mainnet_serum_market_lookup: SerumMarketLookup = SerumMarketLookup.load(
                actual_serum_program_address, SPLTokenLookup.DefaultDataFilepath
            )
            all_market_lookup = CompoundMarketLookup(
                [
                    ids_json_market_lookup,
                    mainnet_overrides_serum_market_lookup,
                    mainnet_serum_market_lookup,
                ]
            )
        elif actual_cluster == "devnet":
            devnet_overrides_serum_market_lookup: SerumMarketLookup = (
                SerumMarketLookup.load(
                    actual_serum_program_address,
                    SPLTokenLookup.DevnetOverridesDataFilepath,
                )
            )
            devnet_serum_market_lookup: SerumMarketLookup = SerumMarketLookup.load(
                actual_serum_program_address, SPLTokenLookup.DevnetDataFilepath
            )
            all_market_lookup = CompoundMarketLookup(
                [
                    ids_json_market_lookup,
                    devnet_overrides_serum_market_lookup,
                    devnet_serum_market_lookup,
                ]
            )
        market_lookup: MarketLookup = all_market_lookup

        actual_monitor_transactions_commitment: Commitment = (
            monitor_transactions_commitment or Finalized
        )
        actual_slot_holder: AbstractSlotHolder = slot_holder or NullSlotHolder()
        actual_monitor_transactions_timeout = monitor_transactions_timeout or 90
        actual_transaction_monitor: TransactionMonitor = NullTransactionMonitor(
            slot_holder=actual_slot_holder
        )
        if monitor_transactions:
            actual_transaction_monitor = WebSocketTransactionMonitor(
                actual_cluster_urls[0].ws,
                commitment=actual_monitor_transactions_commitment,
                transaction_timeout=actual_monitor_transactions_timeout,
                collector=DequeTransactionStatusCollector(),
                slot_holder=actual_slot_holder,
            )

        context = Context(
            actual_name,
            actual_cluster,
            actual_cluster_urls,
            actual_skip_preflight,
            actual_tpu_retransmissions,
            actual_commitment,
            actual_encoding,
            actual_blockhash_cache_duration,
            actual_http_request_timeout,
            actual_stale_data_pauses_before_retry,
            actual_program_address,
            actual_serum_program_address,
            actual_group_name,
            actual_group_address,
            actual_gma_chunk_size,
            actual_gma_chunk_pause,
            actual_reflink,
            instrument_lookup,
            market_lookup,
            actual_transaction_monitor,
        )

        return context
