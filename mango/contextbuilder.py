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

from solana.publickey import PublicKey

from .client import BetterClient
from .constants import MangoConstants
from .context import Context
from .idsjsonmarketlookup import IdsJsonMarketLookup
from .idsjsontokenlookup import IdsJsonTokenLookup
from .marketlookup import CompoundMarketLookup, MarketLookup
from .serummarketlookup import SerumMarketLookup
from .spltokenlookup import SplTokenLookup
from .tokenlookup import TokenLookup, CompoundTokenLookup


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
    def add_command_line_parameters(parser: argparse.ArgumentParser, logging_default=logging.INFO) -> None:
        parser.add_argument("--name", type=str, default="Mango Explorer",
                            help="Name of the program (used in reports and alerts)")
        parser.add_argument("--cluster-name", type=str, default=None, help="Solana RPC cluster name")
        parser.add_argument("--cluster-url", type=str, default=None, help="Solana RPC cluster URL")
        parser.add_argument("--group-name", type=str, default=None, help="Mango group name")
        parser.add_argument("--group-address", type=PublicKey, default=None, help="Mango group address")
        parser.add_argument("--mango-program-address", type=PublicKey, default=None, help="Mango program address")
        parser.add_argument("--serum-program-address", type=PublicKey, default=None, help="Serum program address")
        parser.add_argument("--skip-preflight", default=False, action="store_true", help="Skip pre-flight checks")

        parser.add_argument("--token-data-file", type=str, default=SplTokenLookup.DefaultDataFilepath,
                            help="data file that contains token symbols, names, mints and decimals (format is same as https://raw.githubusercontent.com/solana-labs/token-list/main/src/tokens/solana.tokenlist.json)")

        # This isn't really a Context thing but we don't have a better place for it (yet) and we
        # don't want to duplicate it in every command.
        parser.add_argument("--log-level", default=logging_default, type=lambda level: getattr(logging, level),
                            help="level of verbosity to log (possible values: DEBUG, INFO, WARNING, ERROR, CRITICAL)")

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
        cluster_url: typing.Optional[str] = args.cluster_url
        group_name: typing.Optional[str] = args.group_name
        group_address: typing.Optional[PublicKey] = args.group_address
        mango_program_address: typing.Optional[PublicKey] = args.mango_program_address
        serum_program_address: typing.Optional[PublicKey] = args.serum_program_address
        skip_preflight: bool = bool(args.skip_preflight)
        token_filename: str = args.token_data_file

        return ContextBuilder._build(name, cluster_name, cluster_url, skip_preflight, group_name, group_address, mango_program_address, serum_program_address, token_filename)

    @staticmethod
    def default():
        return ContextBuilder._build(None, None, None, False, None, None, None, None, SplTokenLookup.DefaultDataFilepath)

    @staticmethod
    def from_group_name(context: Context, group_name: str) -> Context:
        return ContextBuilder._build(context.name, context.client.cluster_name, context.client.cluster_url,
                                     context.client.skip_preflight, group_name, None,
                                     None, None, SplTokenLookup.DefaultDataFilepath)

    @staticmethod
    def forced_to_devnet(context: Context) -> Context:
        cluster_name: str = "devnet"
        cluster_url: str = MangoConstants["cluster_urls"][cluster_name]
        fresh_context = copy.copy(context)
        fresh_context.client = BetterClient.from_configuration(context.name,
                                                               cluster_name,
                                                               cluster_url,
                                                               context.client.commitment,
                                                               context.client.skip_preflight,
                                                               context.client.instruction_reporter)

        return fresh_context

    @staticmethod
    def forced_to_mainnet_beta(context: Context) -> Context:
        cluster_name: str = "mainnet"
        cluster_url: str = MangoConstants["cluster_urls"][cluster_name]
        fresh_context = copy.copy(context)
        fresh_context.client = BetterClient.from_configuration(context.name,
                                                               cluster_name,
                                                               cluster_url,
                                                               context.client.commitment,
                                                               context.client.skip_preflight,
                                                               context.client.instruction_reporter)

        return fresh_context

    # This function is the converse of `add_command_line_parameters()` - it takes
    # an argument of parsed command-line parameters and expects to see the ones it added
    # to that collection in the `add_command_line_parameters()` call.
    #
    # It then uses those parameters to create a properly-configured `Context` object.
    #
    @staticmethod
    def _build(name: typing.Optional[str], cluster_name: typing.Optional[str], cluster_url: typing.Optional[str],
               skip_preflight: bool, group_name: typing.Optional[str], group_address: typing.Optional[PublicKey],
               program_address: typing.Optional[PublicKey], serum_program_address: typing.Optional[PublicKey],
               token_filename: str) -> "Context":
        def public_key_or_none(address: typing.Optional[str]) -> typing.Optional[PublicKey]:
            if address is not None and address != "":
                return PublicKey(address)
            return None
        default_group_data = MangoConstants["groups"][0]
        actual_name: str = name or os.environ.get("NAME") or "Mango Explorer"
        actual_cluster: str = cluster_name or os.environ.get("CLUSTER_NAME") or default_group_data["cluster"]
        actual_cluster_url: str = cluster_url or os.environ.get(
            "CLUSTER_URL") or MangoConstants["cluster_urls"][actual_cluster]
        actual_skip_preflight: bool = skip_preflight
        actual_group_name: str = group_name or os.environ.get("GROUP_NAME") or default_group_data["name"]

        found_group_data: typing.Any = None
        for group in MangoConstants["groups"]:
            if group["cluster"] == actual_cluster and group["name"].upper() == actual_group_name.upper():
                found_group_data = group

        if found_group_data is None:
            raise Exception(f"Could not find group named '{actual_group_name}' in cluster '{actual_cluster}'.")

        actual_group_address: PublicKey = group_address or public_key_or_none(os.environ.get(
            "GROUP_ADDRESS")) or PublicKey(found_group_data["publicKey"])
        actual_program_address: PublicKey = program_address or public_key_or_none(os.environ.get(
            "MANGO_PROGRAM_ADDRESS")) or PublicKey(found_group_data["mangoProgramId"])
        actual_serum_program_address: PublicKey = serum_program_address or public_key_or_none(os.environ.get(
            "SERUM_PROGRAM_ADDRESS")) or PublicKey(found_group_data["serumProgramId"])

        ids_json_token_lookup: TokenLookup = IdsJsonTokenLookup(actual_cluster, actual_group_name)
        all_token_lookup = ids_json_token_lookup
        if actual_cluster == "mainnet":
            mainnet_spl_token_lookup: TokenLookup = SplTokenLookup.load(token_filename)
            all_token_lookup = CompoundTokenLookup([ids_json_token_lookup, mainnet_spl_token_lookup])
        elif actual_cluster == "devnet":
            devnet_token_filename = token_filename.rsplit('.', 1)[0] + ".devnet.json"
            devnet_spl_token_lookup: TokenLookup = SplTokenLookup.load(devnet_token_filename)
            all_token_lookup = CompoundTokenLookup([ids_json_token_lookup, devnet_spl_token_lookup])
        token_lookup: TokenLookup = all_token_lookup

        ids_json_market_lookup: MarketLookup = IdsJsonMarketLookup(actual_cluster)
        all_market_lookup = ids_json_market_lookup
        if actual_cluster == "mainnet":
            mainnet_serum_market_lookup: SerumMarketLookup = SerumMarketLookup.load(
                actual_serum_program_address, token_filename)
            all_market_lookup = CompoundMarketLookup([ids_json_market_lookup, mainnet_serum_market_lookup])
        elif actual_cluster == "devnet":
            devnet_token_filename = token_filename.rsplit('.', 1)[0] + ".devnet.json"
            devnet_serum_market_lookup: SerumMarketLookup = SerumMarketLookup.load(
                actual_serum_program_address, devnet_token_filename)
            all_market_lookup = CompoundMarketLookup([ids_json_market_lookup, devnet_serum_market_lookup])
        market_lookup: MarketLookup = all_market_lookup

        return Context(actual_name, actual_cluster, actual_cluster_url, actual_skip_preflight, actual_program_address, actual_serum_program_address, actual_group_name, actual_group_address, token_lookup, market_lookup)
