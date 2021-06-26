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
import time
import typing

from decimal import Decimal
from rx.scheduler import ThreadPoolScheduler
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.rpc.commitment import Commitment
from solana.rpc.types import MemcmpOpts, RPCError, RPCResponse, TxOpts

from .constants import MangoConstants, SOL_DECIMAL_DIVISOR
from .idsjsonmarketlookup import IdsJsonMarketLookup
from .idsjsontokenlookup import IdsJsonTokenLookup
from .marketlookup import CompoundMarketLookup, MarketLookup
from .serummarketlookup import SerumMarketLookup
from .spltokenlookup import SplTokenLookup
from .tokenlookup import TokenLookup, CompoundTokenLookup


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

_default_group_data = MangoConstants["groups"][2]
default_cluster = os.environ.get("CLUSTER") or _default_group_data["cluster"]
default_cluster_url = os.environ.get("CLUSTER_URL") or MangoConstants["cluster_urls"][default_cluster]

default_program_id = PublicKey(_default_group_data["mangoProgramId"])
default_dex_program_id = PublicKey(_default_group_data["serumProgramId"])

default_group_name = os.environ.get("GROUP_NAME") or _default_group_data["name"]
default_group_id = PublicKey(_default_group_data["publicKey"])

# Probably best to access this through the Context object
_pool_scheduler = ThreadPoolScheduler(multiprocessing.cpu_count())

# # 🥭 Context class
#
# A `Context` object to manage Solana connection and Mango configuration.
#


class Context:
    def __init__(self, cluster: str, cluster_url: str, program_id: PublicKey, dex_program_id: PublicKey,
                 group_name: str, group_id: PublicKey, token_filename: str = SplTokenLookup.DefaultDataFilepath):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.cluster: str = cluster
        self.cluster_url: str = cluster_url
        self.client: Client = Client(cluster_url)
        self.program_id: PublicKey = program_id
        self.dex_program_id: PublicKey = dex_program_id
        self.group_name: str = group_name
        self.group_id: PublicKey = group_id
        self.commitment: Commitment = Commitment("processed")
        self.transaction_options: TxOpts = TxOpts(preflight_commitment=self.commitment)
        self.encoding: str = "base64"
        ids_json_token_lookup: TokenLookup = IdsJsonTokenLookup(cluster, group_name)
        spl_token_lookup: TokenLookup = SplTokenLookup.load(token_filename)
        all_token_lookup: TokenLookup = CompoundTokenLookup(
            [ids_json_token_lookup, spl_token_lookup])
        self.token_lookup: TokenLookup = all_token_lookup

        ids_json_market_lookup: MarketLookup = IdsJsonMarketLookup(cluster)
        serum_market_lookup: SerumMarketLookup = SerumMarketLookup.load(token_filename)
        all_market_lookup = CompoundMarketLookup([ids_json_market_lookup, serum_market_lookup])
        self.market_lookup: MarketLookup = all_market_lookup

        # kangda said in Discord: https://discord.com/channels/791995070613159966/836239696467591186/847816026245693451
        # "I think you are better off doing 4,8,16,20,30"
        self.retry_pauses: typing.Sequence[Decimal] = [Decimal(4), Decimal(
            8), Decimal(16), Decimal(20), Decimal(30)]

    @property
    def pool_scheduler(self) -> ThreadPoolScheduler:
        return _pool_scheduler

    @staticmethod
    def default():
        return Context(default_cluster, default_cluster_url, default_program_id,
                       default_dex_program_id, default_group_name, default_group_id)

    def fetch_sol_balance(self, account_public_key: PublicKey) -> Decimal:
        result = self.client.get_balance(account_public_key, commitment=self.commitment)
        value = Decimal(result["result"]["value"])
        return value / SOL_DECIMAL_DIVISOR

    def fetch_program_accounts_for_owner(self, program_id: PublicKey, owner: PublicKey):
        memcmp_opts = [
            MemcmpOpts(offset=40, bytes=str(owner)),
        ]

        return self.client.get_program_accounts(program_id, memcmp_opts=memcmp_opts, commitment=self.commitment, encoding=self.encoding)

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

    def wait_for_confirmation(self, transaction_id: str, max_wait_in_seconds: int = 60) -> typing.Optional[typing.Dict]:
        self.logger.info(
            f"Waiting up to {max_wait_in_seconds} seconds for {transaction_id}.")
        for wait in range(0, max_wait_in_seconds):
            time.sleep(1)
            confirmed = self.client.get_confirmed_transaction(transaction_id)
            if confirmed["result"] is not None:
                self.logger.info(f"Confirmed after {wait} seconds.")
                return confirmed["result"]
        self.logger.info(f"Timed out after {wait} seconds waiting on transaction {transaction_id}.")
        return None

    def new_from_cluster(self, cluster: str) -> "Context":
        cluster_url = MangoConstants["cluster_urls"][cluster]
        for group_data in MangoConstants["groups"]:
            if group_data["cluster"] == cluster:
                if group_data["name"] == self.group_name:
                    program_id = PublicKey(group_data["mangoProgramId"])
                    dex_program_id = PublicKey(group_data["serumProgramId"])
                    group_id = PublicKey(_default_group_data["publicKey"])
                    return Context(cluster, cluster_url, program_id, dex_program_id, self.group_name, group_id)
        raise Exception(f"Could not find group name '{self.group_name}' in cluster '{cluster}'.")

    def new_from_cluster_url(self, cluster_url: str) -> "Context":
        return Context(self.cluster, cluster_url, self.program_id, self.dex_program_id, self.group_name, self.group_id)

    def new_from_group_name(self, group_name: str) -> "Context":
        for group_data in MangoConstants["groups"]:
            if group_data["cluster"] == self.cluster:
                if group_data["name"] == group_name:
                    program_id = PublicKey(group_data["mangoProgramId"])
                    dex_program_id = PublicKey(group_data["serumProgramId"])
                    group_id = PublicKey(_default_group_data["publicKey"])
                    return Context(self.cluster, self.cluster_url, program_id, dex_program_id, group_name, group_id)
        raise Exception(f"Could not find group name '{group_name}' in cluster '{self.cluster}'.")

    def new_from_group_id(self, group_id: PublicKey) -> "Context":
        group_id_str = str(group_id)
        for group_data in MangoConstants["groups"]:
            if group_data["cluster"] == self.cluster:
                if group_data["publicKey"] == group_id_str:
                    program_id = PublicKey(group_data["mangoProgramId"])
                    dex_program_id = PublicKey(group_data["serumProgramId"])
                    group_id = PublicKey(_default_group_data["publicKey"])
                    group_name = _default_group_data["name"]
                    return Context(self.cluster, self.cluster_url, program_id, dex_program_id, group_name, group_id)
        raise Exception(f"Could not find group with ID '{group_id}' in cluster '{self.cluster}'.")

    @staticmethod
    def from_cluster_and_group_name(cluster: str, group_name: str) -> "Context":
        cluster_url = MangoConstants["cluster_urls"][cluster]
        program_id = PublicKey(MangoConstants[cluster]["mango_program_id"])
        dex_program_id = PublicKey(MangoConstants[cluster]["dex_program_id"])
        group_id = PublicKey(MangoConstants[cluster]["mango_groups"][group_name]["mango_group_pk"])

        return Context(cluster, cluster_url, program_id, dex_program_id, group_name, group_id)

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
        group_id = args.group_id
        if (args.group_name != default_group_name) and (group_id == default_group_id):
            for group in MangoConstants["groups"]:
                if group["cluster"] == args.cluster and group["name"].upper() == args.group_name.upper():
                    group_id = PublicKey(group["publicKey"])
        elif (args.cluster != default_cluster) and (group_id == default_group_id):
            for group in MangoConstants["groups"]:
                if group["cluster"] == args.cluster and group["name"].upper() == args.group_name.upper():
                    group_id = PublicKey(group["publicKey"])

        # Same problem here, but with cluster names and URLs. We want someone to be able to change the
        # cluster just by changing the cluster name.
        cluster_url = args.cluster_url
        if (args.cluster != default_cluster) and (cluster_url == default_cluster_url):
            cluster_url = MangoConstants["cluster_urls"][args.cluster]

        program_id = args.program_id
        if group_id == PublicKey("7pVYhpKUHw88neQHxgExSH6cerMZ1Axx1ALQP9sxtvQV"):
            program_id = PublicKey("JD3bq9hGdy38PuWQ4h2YJpELmHVGPPfFSuFkpzAd9zfu")

        return Context(args.cluster, cluster_url, program_id, args.dex_program_id, args.group_name, group_id)

    def __str__(self) -> str:
        return f"""« 𝙲𝚘𝚗𝚝𝚎𝚡𝚝:
    Cluster: {self.cluster}
    Cluster URL: {self.cluster_url}
    Program ID: {self.program_id}
    DEX Program ID: {self.dex_program_id}
    Group Name: {self.group_name}
    Group ID: {self.group_id}
»"""

    def __repr__(self) -> str:
        return f"{self}"
