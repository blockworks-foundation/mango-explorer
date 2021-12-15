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
import copy
import logging
import os
import typing

from decimal import Decimal
from solana.publickey import PublicKey

from .client import BetterClient
from .constants import MangoConstants, DATA_PATH
from .context import Context
from .idsjsonmarketlookup import IdsJsonMarketLookup
from .instrumentlookup import InstrumentLookup, CompoundInstrumentLookup, IdsJsonTokenLookup, NonSPLInstrumentLookup, SPLTokenLookup
from .marketlookup import CompoundMarketLookup, MarketLookup
from .serummarketlookup import SerumMarketLookup


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


# # 🥭 ContextBuilder class
#
# A `ContextBuilder` class to allow building `Context` objects without introducing circular dependencies.
#
class ContextBuilder:
    # Configuring a `Context` is a common operation for command-line programs and can involve a
    # lot of duplicate code.
    #
    # This function centralises some of it to ensure consistency and readability.
    #
    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--name", type=str, default="Mango Explorer",
                            help="Name of the program (used in reports and alerts)")
        parser.add_argument("--cluster-name", type=str, default=None, help="Solana RPC cluster name")
        parser.add_argument("--cluster-url", type=str, action="append", default=[],
                            help="Solana RPC cluster URL (can be specified multiple times to provide failover when one errors)")
        parser.add_argument("--group-name", type=str, default=None, help="Mango group name")
        parser.add_argument("--group-address", type=PublicKey, default=None, help="Mango group address")
        parser.add_argument("--mango-program-address", type=PublicKey, default=None, help="Mango program address")
        parser.add_argument("--serum-program-address", type=PublicKey, default=None, help="Serum program address")
        parser.add_argument("--skip-preflight", default=False, action="store_true", help="Skip pre-flight checks")
        parser.add_argument("--commitment", type=str, default=None,
                            help="Commitment to use when sending transactions (can be 'finalized', 'confirmed' or 'processed')")
        parser.add_argument("--encoding", type=str, default=None,
                            help="Encoding to request when receiving data from Solana (options are 'base58' (slow), 'base64', 'base64+zstd', or 'jsonParsed')")
        parser.add_argument("--blockhash-cache-duration", type=int,
                            help="How long (in seconds) to cache 'recent' blockhashes")
        parser.add_argument("--stale-data-pause-before-retry", type=Decimal,
                            help="How long (in seconds, e.g. 0.1) to pause after retrieving stale data before retrying")
        parser.add_argument("--stale-data-maximum-retries", type=int,
                            help="How many times to retry fetching data after being given stale data before giving up")
        parser.add_argument("--gma-chunk-size", type=Decimal, default=None,
                            help="Maximum number of addresses to send in a single call to getMultipleAccounts()")
        parser.add_argument("--gma-chunk-pause", type=Decimal, default=None,
                            help="number of seconds to pause between successive getMultipleAccounts() calls to avoid rate limiting")

        parser.add_argument("--token-data-file", type=str, default=SPLTokenLookup.DefaultDataFilepath,
                            help="data file that contains token symbols, names, mints and decimals (format is same as https://raw.githubusercontent.com/solana-labs/token-list/main/src/tokens/solana.tokenlist.json)")

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
        cluster_urls: typing.Optional[typing.Sequence[str]] = args.cluster_url
        group_name: typing.Optional[str] = args.group_name
        group_address: typing.Optional[PublicKey] = args.group_address
        mango_program_address: typing.Optional[PublicKey] = args.mango_program_address
        serum_program_address: typing.Optional[PublicKey] = args.serum_program_address
        skip_preflight: bool = bool(args.skip_preflight)
        commitment: typing.Optional[str] = args.commitment
        encoding: typing.Optional[str] = args.encoding
        blockhash_cache_duration: typing.Optional[int] = args.blockhash_cache_duration
        stale_data_pause_before_retry: typing.Optional[Decimal] = args.stale_data_pause_before_retry
        stale_data_maximum_retries: typing.Optional[int] = args.stale_data_maximum_retries
        gma_chunk_size: typing.Optional[Decimal] = args.gma_chunk_size
        gma_chunk_pause: typing.Optional[Decimal] = args.gma_chunk_pause
        token_filename: str = args.token_data_file

        # Do this here so build() only ever has to handle the sequence of retry times. (It gets messy
        # passing around the sequnce *plus* the data to reconstruct it for build().)
        actual_maximum_stale_data_pauses: int = stale_data_maximum_retries or 20
        actual_stale_data_pauses_before_retry: typing.Sequence[float] = []
        if stale_data_pause_before_retry is not None:
            actual_stale_data_pauses_before_retry = [
                float(stale_data_pause_before_retry)] * actual_maximum_stale_data_pauses

        context: Context = ContextBuilder.build(name, cluster_name, cluster_urls, skip_preflight, commitment,
                                                encoding, blockhash_cache_duration,
                                                actual_stale_data_pauses_before_retry,
                                                group_name, group_address, mango_program_address,
                                                serum_program_address, gma_chunk_size, gma_chunk_pause,
                                                token_filename)
        logging.debug(f"{context}")

        return context

    @staticmethod
    def default() -> Context:
        return ContextBuilder.build()

    @staticmethod
    def from_group_name(context: Context, group_name: str) -> Context:
        return ContextBuilder.build(context.name, context.client.cluster_name, context.client.cluster_urls,
                                    context.client.skip_preflight, context.client.commitment,
                                    context.client.encoding, context.client.blockhash_cache_duration,
                                    context.client.stale_data_pauses_before_retry,
                                    group_name, None, None, None,
                                    context.gma_chunk_size, context.gma_chunk_pause,
                                    SPLTokenLookup.DefaultDataFilepath)

    @staticmethod
    def forced_to_devnet(context: Context) -> Context:
        cluster_name: str = "devnet"
        cluster_url: str = MangoConstants["cluster_urls"][cluster_name]
        fresh_context = copy.copy(context)
        fresh_context.client = BetterClient.from_configuration(context.name,
                                                               cluster_name,
                                                               [cluster_url],
                                                               context.client.commitment,
                                                               context.client.skip_preflight,
                                                               context.client.encoding,
                                                               context.client.blockhash_cache_duration,
                                                               context.client.stale_data_pauses_before_retry,
                                                               context.client.instruction_reporter)

        return fresh_context

    @staticmethod
    def forced_to_mainnet_beta(context: Context) -> Context:
        cluster_name: str = "mainnet"
        cluster_url: str = MangoConstants["cluster_urls"][cluster_name]
        fresh_context = copy.copy(context)
        fresh_context.client = BetterClient.from_configuration(context.name,
                                                               cluster_name,
                                                               [cluster_url],
                                                               context.client.commitment,
                                                               context.client.skip_preflight,
                                                               context.client.encoding,
                                                               context.client.blockhash_cache_duration,
                                                               context.client.stale_data_pauses_before_retry,
                                                               context.client.instruction_reporter)

        return fresh_context

    @staticmethod
    def build(name: typing.Optional[str] = None, cluster_name: typing.Optional[str] = None,
              cluster_urls: typing.Optional[typing.Sequence[str]] = None, skip_preflight: bool = False,
              commitment: typing.Optional[str] = None, encoding: typing.Optional[str] = None,
              blockhash_cache_duration: typing.Optional[int] = None,
              stale_data_pauses_before_retry: typing.Optional[typing.Sequence[float]] = None,
              group_name: typing.Optional[str] = None, group_address: typing.Optional[PublicKey] = None,
              program_address: typing.Optional[PublicKey] = None, serum_program_address: typing.Optional[PublicKey] = None,
              gma_chunk_size: typing.Optional[Decimal] = None, gma_chunk_pause: typing.Optional[Decimal] = None,
              token_filename: str = SPLTokenLookup.DefaultDataFilepath) -> "Context":
        def __public_key_or_none(address: typing.Optional[str]) -> typing.Optional[PublicKey]:
            if address is not None and address != "":
                return PublicKey(address)
            return None
        # The first group is only used to determine the default cluster if it is not otherwise specified.
        first_group_data = MangoConstants["groups"][0]
        actual_name: str = name or os.environ.get("NAME") or "Mango Explorer"
        actual_cluster: str = cluster_name or os.environ.get("CLUSTER_NAME") or first_group_data["cluster"]

        # Now that we have the actual cluster name, taking environment variables and defaults into account,
        # we can decide what we want as the default group.
        for group_data in MangoConstants["groups"]:
            if group_data["cluster"] == actual_cluster:
                default_group_data = group_data
                break

        actual_commitment: str = commitment or "processed"
        actual_encoding: str = encoding or "base64"
        actual_blockhash_cache_duration: int = blockhash_cache_duration or 0
        actual_stale_data_pauses_before_retry: typing.Sequence[float] = stale_data_pauses_before_retry or []

        actual_cluster_urls: typing.Optional[typing.Sequence[str]] = cluster_urls
        if actual_cluster_urls is None or len(actual_cluster_urls) == 0:
            cluster_url_from_environment: typing.Optional[str] = os.environ.get("CLUSTER_URL")
            if cluster_url_from_environment is not None and cluster_url_from_environment != "":
                actual_cluster_urls = [cluster_url_from_environment]
            else:
                actual_cluster_urls = [MangoConstants["cluster_urls"][actual_cluster]]

        actual_skip_preflight: bool = skip_preflight
        actual_group_name: str = group_name or os.environ.get("GROUP_NAME") or default_group_data["name"]

        found_group_data: typing.Any = None
        for group in MangoConstants["groups"]:
            if group["cluster"] == actual_cluster and group["name"].upper() == actual_group_name.upper():
                found_group_data = group

        if found_group_data is None:
            raise Exception(f"Could not find group named '{actual_group_name}' in cluster '{actual_cluster}'.")

        actual_group_address: PublicKey = group_address or __public_key_or_none(os.environ.get(
            "GROUP_ADDRESS")) or PublicKey(found_group_data["publicKey"])
        actual_program_address: PublicKey = program_address or __public_key_or_none(os.environ.get(
            "MANGO_PROGRAM_ADDRESS")) or PublicKey(found_group_data["mangoProgramId"])
        actual_serum_program_address: PublicKey = serum_program_address or __public_key_or_none(os.environ.get(
            "SERUM_PROGRAM_ADDRESS")) or PublicKey(found_group_data["serumProgramId"])

        actual_gma_chunk_size: Decimal = gma_chunk_size or Decimal(100)
        actual_gma_chunk_pause: Decimal = gma_chunk_pause or Decimal(0)

        ids_json_token_lookup: InstrumentLookup = IdsJsonTokenLookup(actual_cluster, actual_group_name)
        instrument_lookup: InstrumentLookup = ids_json_token_lookup
        mainnet_overrides_filename = os.path.join(DATA_PATH, "overrides.tokenlist.json")
        devnet_overrides_filename = os.path.join(DATA_PATH, "overrides.tokenlist.devnet.json")
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
            mainnet_overrides_token_lookup: InstrumentLookup = SPLTokenLookup.load(mainnet_overrides_filename)
            mainnet_spl_token_lookup: InstrumentLookup = SPLTokenLookup.load(token_filename)
            mainnet_non_spl_instrument_lookup: InstrumentLookup = NonSPLInstrumentLookup.load(
                NonSPLInstrumentLookup.DefaultMainnetDataFilepath)
            instrument_lookup = CompoundInstrumentLookup([
                ids_json_token_lookup,
                mainnet_overrides_token_lookup,
                mainnet_non_spl_instrument_lookup,
                mainnet_spl_token_lookup])
        elif actual_cluster == "devnet":
            devnet_overrides_token_lookup: InstrumentLookup = SPLTokenLookup.load(devnet_overrides_filename)
            devnet_token_filename = token_filename.rsplit('.', 1)[0] + ".devnet.json"
            devnet_spl_token_lookup: InstrumentLookup = SPLTokenLookup.load(devnet_token_filename)
            devnet_non_spl_instrument_lookup: InstrumentLookup = NonSPLInstrumentLookup.load(
                NonSPLInstrumentLookup.DefaultDevnetDataFilepath)
            instrument_lookup = CompoundInstrumentLookup([
                ids_json_token_lookup,
                devnet_overrides_token_lookup,
                devnet_non_spl_instrument_lookup,
                devnet_spl_token_lookup])

        ids_json_market_lookup: MarketLookup = IdsJsonMarketLookup(actual_cluster, instrument_lookup)
        all_market_lookup = ids_json_market_lookup
        if actual_cluster == "mainnet":
            mainnet_overrides_serum_market_lookup: SerumMarketLookup = SerumMarketLookup.load(
                actual_serum_program_address, mainnet_overrides_filename)
            mainnet_serum_market_lookup: SerumMarketLookup = SerumMarketLookup.load(
                actual_serum_program_address, token_filename)
            all_market_lookup = CompoundMarketLookup([
                ids_json_market_lookup,
                mainnet_overrides_serum_market_lookup,
                mainnet_serum_market_lookup])
        elif actual_cluster == "devnet":
            devnet_overrides_serum_market_lookup: SerumMarketLookup = SerumMarketLookup.load(
                actual_serum_program_address, devnet_overrides_filename)
            devnet_token_filename = token_filename.rsplit('.', 1)[0] + ".devnet.json"
            devnet_serum_market_lookup: SerumMarketLookup = SerumMarketLookup.load(
                actual_serum_program_address, devnet_token_filename)
            all_market_lookup = CompoundMarketLookup([
                ids_json_market_lookup,
                devnet_overrides_serum_market_lookup,
                devnet_serum_market_lookup])
        market_lookup: MarketLookup = all_market_lookup

        return Context(actual_name, actual_cluster, actual_cluster_urls, actual_skip_preflight, actual_commitment, actual_encoding, actual_blockhash_cache_duration, actual_stale_data_pauses_before_retry, actual_program_address, actual_serum_program_address, actual_group_name, actual_group_address, actual_gma_chunk_size, actual_gma_chunk_pause, instrument_lookup, market_lookup)
