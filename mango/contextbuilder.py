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

from solana.publickey import PublicKey

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
# * CLUSTER (defaults to: mainnet)
# * CLUSTER_URL (defaults to URL for RPC server for CLUSTER defined in `ids.json`)
# * GROUP_NAME (defaults to: BTC_ETH_USDT)
#

default_name: str = os.environ.get("NAME") or "Mango Explorer"
default_skip_preflight: bool = False

_default_group_data = MangoConstants["groups"][0]
default_cluster: str = os.environ.get("CLUSTER") or _default_group_data["cluster"]
default_cluster_url: str = os.environ.get("CLUSTER_URL") or MangoConstants["cluster_urls"][default_cluster]

default_program_id: PublicKey = PublicKey(_default_group_data["mangoProgramId"])
default_dex_program_id: PublicKey = PublicKey(_default_group_data["serumProgramId"])

default_group_name: str = os.environ.get("GROUP_NAME") or _default_group_data["name"]
default_group_id: PublicKey = PublicKey(_default_group_data["publicKey"])

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
        parser.add_argument("--name", type=str, default=default_name,
                            help="Name of the program (used in reports and alerts)")
        parser.add_argument("--cluster", type=str, default=default_cluster,
                            help="Solana RPC cluster name")
        parser.add_argument("--cluster-url", type=str, default=default_cluster_url,
                            help="Solana RPC cluster URL")
        parser.add_argument("--skip-preflight", default=default_skip_preflight, action="store_true",
                            help="Skip Solana pre-flight checks")
        parser.add_argument("--program-id", type=PublicKey, default=default_program_id,
                            help="Mango program ID/address")
        parser.add_argument("--dex-program-id", type=PublicKey, default=default_dex_program_id,
                            help="DEX program ID/address")
        parser.add_argument("--group-name", type=str, default=default_group_name,
                            help="Mango group name")
        parser.add_argument("--group-id", type=PublicKey, default=default_group_id,
                            help="Mango group ID/address")

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
    def from_command_line_parameters(args: argparse.Namespace) -> "Context":
        # Here we should have values for all our parameters (because they'll either be specified
        # on the command-line or will be the default_* value) but we may be in the situation where
        # a group name is specified but not a group ID, and in that case we want to look up the
        # group ID.
        #
        # In that situation, the group_name will not be default_group_name but the group_id will
        # still be default_group_id. In that situation we want to override what we were passed
        # as the group_id.
        name: str = args.name
        group_name: str = args.group_name
        cluster: str = args.cluster
        cluster_url: str = args.cluster_url
        skip_preflight: bool = args.skip_preflight
        token_filename: str = args.token_data_file
        group_id: PublicKey = args.group_id
        program_id: PublicKey = args.program_id
        dex_program_id: PublicKey = args.dex_program_id

        return ContextBuilder._build(name, cluster, cluster_url, skip_preflight, group_name, group_id, program_id, dex_program_id, token_filename)

    @staticmethod
    def default():
        return ContextBuilder._build(default_name, default_cluster, default_cluster_url,
                                     default_skip_preflight, default_group_name, default_group_id,
                                     default_program_id, default_dex_program_id,
                                     SplTokenLookup.DefaultDataFilepath)

    # This function is the converse of `add_command_line_parameters()` - it takes
    # an argument of parsed command-line parameters and expects to see the ones it added
    # to that collection in the `add_command_line_parameters()` call.
    #
    # It then uses those parameters to create a properly-configured `Context` object.
    #
    @staticmethod
    def _build(name: str, cluster: str, cluster_url: str, skip_preflight: bool, group_name: str, group_id: PublicKey, program_id: PublicKey, dex_program_id: PublicKey, token_filename: str) -> "Context":
        ids_json_token_lookup: TokenLookup = IdsJsonTokenLookup(cluster, group_name)
        all_token_lookup = ids_json_token_lookup
        if cluster == "mainnet":
            mainnet_spl_token_lookup: TokenLookup = SplTokenLookup.load(token_filename)
            all_token_lookup = CompoundTokenLookup([ids_json_token_lookup, mainnet_spl_token_lookup])
        elif cluster == "devnet":
            devnet_token_filename = token_filename.rsplit('.', 1)[0] + ".devnet.json"
            devnet_spl_token_lookup: TokenLookup = SplTokenLookup.load(devnet_token_filename)
            all_token_lookup = CompoundTokenLookup([ids_json_token_lookup, devnet_spl_token_lookup])
        token_lookup: TokenLookup = all_token_lookup

        ids_json_market_lookup: MarketLookup = IdsJsonMarketLookup(cluster)
        all_market_lookup = ids_json_market_lookup
        if cluster == "mainnet":
            mainnet_serum_market_lookup: SerumMarketLookup = SerumMarketLookup.load(dex_program_id, token_filename)
            all_market_lookup = CompoundMarketLookup([ids_json_market_lookup, mainnet_serum_market_lookup])
        elif cluster == "devnet":
            devnet_token_filename = token_filename.rsplit('.', 1)[0] + ".devnet.json"
            devnet_serum_market_lookup: SerumMarketLookup = SerumMarketLookup.load(
                dex_program_id, devnet_token_filename)
            all_market_lookup = CompoundMarketLookup([ids_json_market_lookup, devnet_serum_market_lookup])
        market_lookup: MarketLookup = all_market_lookup

        if (group_name != default_group_name) and (group_id == default_group_id):
            for group in MangoConstants["groups"]:
                if group["cluster"] == cluster and group["name"].upper() == group_name.upper():
                    group_id = PublicKey(group["publicKey"])
        elif (cluster != default_cluster) and (group_id == default_group_id):
            for group in MangoConstants["groups"]:
                if group["cluster"] == cluster and group["name"].upper() == group_name.upper():
                    group_id = PublicKey(group["publicKey"])

        # Same problem here, but with cluster names and URLs. We want someone to be able to change the
        # cluster just by changing the cluster name.
        if (cluster != default_cluster) and (cluster_url == default_cluster_url):
            cluster_url = MangoConstants["cluster_urls"][cluster]

        return Context(name, cluster, cluster_url, skip_preflight, program_id, dex_program_id, group_name, group_id, token_lookup, market_lookup)
