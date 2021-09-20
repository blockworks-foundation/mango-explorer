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
import multiprocessing
import os
import random
import typing

from decimal import Decimal
from rx.scheduler import ThreadPoolScheduler
from solana.publickey import PublicKey
from solana.rpc.commitment import Commitment
from solana.rpc.types import RPCError, RPCResponse, TxOpts

from .client import BetterClient
from .constants import MangoConstants
from .market import CompoundMarketLookup, MarketLookup
from .spotmarket import SpotMarketLookup
from .token import TokenLookup


# # 🥭 Context
#
# ## Environment Variables
#
# It's possible to override the values in the `Context` variables provided. This can be easier than creating
# the `Context` in code or introducing dependencies and configuration.
#
# The following environment variables are read:
# * CLUSTER (defaults to: mainnet-beta)
# * CLUSTER_URL (defaults to URL for RPC server for CLUSTER defined in `ids.json`)
# * GROUP_NAME (defaults to: BTC_ETH_USDT)
#

default_cluster: str = os.environ.get("CLUSTER") or "mainnet-beta"
default_cluster_url: str = os.environ.get("CLUSTER_URL") or MangoConstants["cluster_urls"][default_cluster]
default_skip_preflight: bool = False
default_commitment: str = "processed"
default_encoding: str = "base64"

default_program_id: PublicKey = PublicKey(MangoConstants[default_cluster]["mango_program_id"])
default_dex_program_id: PublicKey = PublicKey(MangoConstants[default_cluster]["dex_program_id"])

default_group_name: str = os.environ.get("GROUP_NAME") or "BTC_ETH_SOL_SRM_USDC"
default_group_id: PublicKey = PublicKey(
    MangoConstants[default_cluster]["mango_groups"][default_group_name]["mango_group_pk"])

default_gma_chunk_size: Decimal = Decimal(100)
default_gma_chunk_pause: Decimal = Decimal(0)


# The old program ID is used for the 3-token Group, but since the program ID is stored
# in ids.json per cluster, it's not currently possible to put it in that (shared) file.
#
# We keep it here and do some special processing with it.
#
_OLD_3_TOKEN_GROUP_ID = PublicKey("7pVYhpKUHw88neQHxgExSH6cerMZ1Axx1ALQP9sxtvQV")
_OLD_3_TOKEN_PROGRAM_ID = PublicKey("JD3bq9hGdy38PuWQ4h2YJpELmHVGPPfFSuFkpzAd9zfu")

# Probably best to access this through the Context object
_pool_scheduler = ThreadPoolScheduler(multiprocessing.cpu_count())


# # 🥭 Context class
#
# A `Context` object to manage Solana connection and Mango configuration.
#
class Context:
    def __init__(self, cluster: str, cluster_url: str, commitment: str,
                 encoding: str, skip_preflight: bool, program_id: PublicKey,
                 dex_program_id: PublicKey, group_name: str, group_id: PublicKey,
                 gma_chunk_size: Decimal, gma_chunk_pause: Decimal,
                 token_filename: str = TokenLookup.DEFAULT_FILE_NAME):
        configured_program_id = program_id
        if group_id == _OLD_3_TOKEN_GROUP_ID:
            configured_program_id = _OLD_3_TOKEN_PROGRAM_ID

        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.client: BetterClient = BetterClient.from_configuration(
            "Mango Explorer", cluster, cluster_url, Commitment(commitment), encoding, skip_preflight)
        self.cluster: str = cluster
        self.cluster_url: str = cluster_url
        self.program_id: PublicKey = configured_program_id
        self.dex_program_id: PublicKey = dex_program_id
        self.group_name: str = group_name
        self.group_id: PublicKey = group_id
        self.gma_chunk_size: Decimal = gma_chunk_size
        self.gma_chunk_pause: Decimal = gma_chunk_pause
        self.transaction_options: TxOpts = TxOpts(
            preflight_commitment=self.client.commitment, skip_preflight=skip_preflight)
        self.token_lookup: TokenLookup = TokenLookup.load(token_filename)

        spot_market_lookup: SpotMarketLookup = SpotMarketLookup.load(token_filename)
        all_market_lookup = CompoundMarketLookup([spot_market_lookup])
        self.market_lookup: MarketLookup = all_market_lookup

        # kangda said in Discord: https://discord.com/channels/791995070613159966/836239696467591186/847816026245693451
        # "I think you are better off doing 4,8,16,20,30"
        self.retry_pauses: typing.List[Decimal] = [Decimal(4), Decimal(
            8), Decimal(16), Decimal(20), Decimal(30)]

    @property
    def pool_scheduler(self) -> ThreadPoolScheduler:
        return _pool_scheduler

    @staticmethod
    def default():
        return Context(default_cluster, default_cluster_url, default_commitment, default_encoding,
                       default_skip_preflight, default_program_id, default_dex_program_id, default_group_name,
                       default_group_id, default_gma_chunk_size, default_gma_chunk_pause)

    def fetch_sol_balance(self, account_public_key: PublicKey) -> Decimal:
        return self.client.get_balance(account_public_key, commitment=self.client.commitment)

    def unwrap_or_raise_exception(self, response: RPCResponse) -> typing.Any:
        if "error" in response:
            if response["error"] is str:
                message: str = typing.cast(str, response["error"])
                code: int = -1
            else:
                error: RPCError = typing.cast(RPCError, response["error"])
                message = error["message"]
                code = error["code"]
            raise Exception(
                f"Error response from server: '{message}', code: {code}")

        return response["result"]

    def unwrap_transaction_id_or_raise_exception(self, response: RPCResponse) -> str:
        return typing.cast(str, self.unwrap_or_raise_exception(response))

    def random_client_id(self) -> int:
        # 9223372036854775807 is sys.maxsize for 64-bit systems, with a bit_length of 63.
        # We explicitly want to use a max of 64-bits though, so we use the number instead of
        # sys.maxsize, which could be lower on 32-bit systems or higher on 128-bit systems.
        return random.randrange(9223372036854775807)

    @staticmethod
    def _lookup_name_by_address(address: PublicKey, collection: typing.Dict[str, str]) -> typing.Optional[str]:
        address_string = str(address)
        for stored_name, stored_address in collection.items():
            if stored_address == address_string:
                return stored_name
        return None

    @staticmethod
    def _lookup_address_by_name(name: str, collection: typing.Dict[str, str]) -> typing.Optional[PublicKey]:
        for stored_name, stored_address in collection.items():
            if stored_name == name:
                return PublicKey(stored_address)
        return None

    def lookup_group_name(self, group_address: PublicKey) -> str:
        for name, values in MangoConstants[self.cluster]["mango_groups"].items():
            if values["mango_group_pk"] == str(group_address):
                return name
        return "« Unknown Group »"

    def lookup_oracle_name(self, token_address: PublicKey) -> str:
        return Context._lookup_name_by_address(token_address, MangoConstants[self.cluster]["oracles"]) or "« Unknown Oracle »"

    def new_from_cluster(self, cluster: str) -> "Context":
        cluster_url = MangoConstants["cluster_urls"][cluster]
        program_id = PublicKey(MangoConstants[cluster]["mango_program_id"])
        dex_program_id = PublicKey(MangoConstants[cluster]["dex_program_id"])
        group_id = PublicKey(MangoConstants[cluster]["mango_groups"][self.group_name]["mango_group_pk"])

        return Context(cluster, cluster_url, self.client.commitment, self.client.encoding, self.client.skip_preflight, program_id, dex_program_id, self.group_name, group_id, self.gma_chunk_size, self.gma_chunk_pause)

    def new_from_cluster_url(self, cluster_url: str) -> "Context":
        return Context(self.cluster, cluster_url, self.client.commitment, self.client.encoding, self.client.skip_preflight, self.program_id, self.dex_program_id, self.group_name, self.group_id, self.gma_chunk_size, self.gma_chunk_pause)

    def new_from_group_name(self, group_name: str) -> "Context":
        group_id = PublicKey(MangoConstants[self.cluster]["mango_groups"][group_name]["mango_group_pk"])

        # If this Context had the old 3-token Group, we need to override it's program ID.
        program_id = self.program_id
        if self.group_id == _OLD_3_TOKEN_GROUP_ID:
            program_id = PublicKey(MangoConstants[self.cluster]["mango_program_id"])

        return Context(self.cluster, self.cluster_url, self.client.commitment, self.client.encoding, self.client.skip_preflight, program_id, self.dex_program_id, group_name, group_id, self.gma_chunk_size, self.gma_chunk_pause)

    def new_from_group_id(self, group_id: PublicKey) -> "Context":
        actual_group_name = "« Unknown Group »"
        group_id_str = str(group_id)
        for group_name in MangoConstants[self.cluster]["mango_groups"]:
            if MangoConstants[self.cluster]["mango_groups"][group_name]["mango_group_pk"] == group_id_str:
                actual_group_name = group_name
                break

        # If this Context had the old 3-token Group, we need to override it's program ID.
        program_id = self.program_id
        if self.group_id == _OLD_3_TOKEN_GROUP_ID:
            program_id = PublicKey(MangoConstants[self.cluster]["mango_program_id"])

        return Context(self.cluster, self.cluster_url, self.client.commitment, self.client.encoding, self.client.skip_preflight, program_id, self.dex_program_id, actual_group_name, group_id, self.gma_chunk_size, self.gma_chunk_pause)

    # Configuring a `Context` is a common operation for command-line programs and can involve a
    # lot of duplicate code.
    #
    # This function centralises some of it to ensure consistency and readability.
    #
    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser, logging_default=logging.INFO) -> None:
        parser.add_argument("--cluster", type=str, default=default_cluster,
                            help="Solana RPC cluster name")
        parser.add_argument("--cluster-url", type=str, default=default_cluster_url,
                            help="Solana RPC cluster URL")
        parser.add_argument("--program-id", type=str, default=default_program_id,
                            help="Mango program ID/address")
        parser.add_argument("--dex-program-id", type=str, default=default_dex_program_id,
                            help="DEX program ID/address")
        parser.add_argument("--group-name", type=str, default=default_group_name,
                            help="Mango group name")
        parser.add_argument("--group-id", type=str, default=default_group_id,
                            help="Mango group ID/address")
        parser.add_argument("--gma-chunk-size", type=Decimal, default=default_gma_chunk_size,
                            help="Maximum number of addresses to send in a single call to getMultipleAccounts()")
        parser.add_argument("--gma-chunk-pause", type=Decimal, default=default_gma_chunk_pause,
                            help="number of seconds to pause between successive getMultipleAccounts() calls to avoid rate limiting")
        parser.add_argument("--commitment", type=str, default=default_commitment,
                            help="Commitment to use when sending transactions (can be 'finalized', 'confirmed' or 'processed')")
        parser.add_argument("--encoding", type=str, default=default_encoding,
                            help="Encoding to request when receiving data from Solana (options are 'base58' (slow), 'base64', 'base64+zstd', or 'jsonParsed')")
        parser.add_argument("--skip-preflight", default=default_skip_preflight,
                            action="store_true", help="Skip pre-flight checks")
        parser.add_argument("--token-data-file", type=str, default="solana.tokenlist.json",
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
        group_id = args.group_id
        if (args.group_name != default_group_name) and (group_id == default_group_id):
            group_id = PublicKey(MangoConstants[args.cluster]["mango_groups"][args.group_name]["mango_group_pk"])

        # Same problem here, but with cluster names and URLs. We want someone to be able to change the
        # cluster just by changing the cluster name.
        cluster_url = args.cluster_url
        if (args.cluster != default_cluster) and (cluster_url == default_cluster_url):
            cluster_url = MangoConstants["cluster_urls"][args.cluster]

        program_id = args.program_id
        if group_id == PublicKey("7pVYhpKUHw88neQHxgExSH6cerMZ1Axx1ALQP9sxtvQV"):
            program_id = PublicKey("JD3bq9hGdy38PuWQ4h2YJpELmHVGPPfFSuFkpzAd9zfu")

        return Context(args.cluster, cluster_url, args.commitment, args.encoding, args.skip_preflight, program_id, args.dex_program_id, args.group_name, group_id, args.gma_chunk_size, args.gma_chunk_pause)

    def __str__(self) -> str:
        return f"""« 𝙲𝚘𝚗𝚝𝚎𝚡𝚝:
    Cluster: {self.cluster}
    Cluster URL: {self.cluster_url}
    Commitment: {self.client.commitment}
    Encoding: {self.client.encoding}
    Skip Preflight: {self.client.skip_preflight}
    Program ID: {self.program_id}
    DEX Program ID: {self.dex_program_id}
    Group Name: {self.group_name}
    Group ID: {self.group_id}
    Get Multiple Accounts: {self.gma_chunk_size} per call, {self.gma_chunk_pause} between calls
»"""

    def __repr__(self) -> str:
        return f"{self}"
