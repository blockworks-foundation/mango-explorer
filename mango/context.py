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
import random
import typing

from decimal import Decimal
from rx.scheduler import ThreadPoolScheduler
from solana.publickey import PublicKey
from solana.rpc.commitment import Commitment

from .client import BetterClient
from .constants import MangoConstants
from .instructionreporter import InstructionReporter, CompoundInstructionReporter
from .marketlookup import MarketLookup
from .tokenlookup import TokenLookup


# Probably best to access this through the Context object
_pool_scheduler = ThreadPoolScheduler(multiprocessing.cpu_count())

# # 🥭 Context class
#
# A `Context` object to manage Solana connection and Mango configuration.
#


class Context:
    def __init__(self, name: str, cluster: str, cluster_url: str, skip_preflight: bool, program_id: PublicKey, dex_program_id: PublicKey,
                 group_name: str, group_id: PublicKey, token_lookup: TokenLookup, market_lookup: MarketLookup):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.name: str = name
        instruction_reporter: InstructionReporter = CompoundInstructionReporter.from_ids(program_id, dex_program_id)
        self.client: BetterClient = BetterClient.from_configuration(
            name, cluster, cluster_url, Commitment("processed"), skip_preflight, instruction_reporter)
        self.program_id: PublicKey = program_id
        self.dex_program_id: PublicKey = dex_program_id
        self.group_name: str = group_name
        self.group_id: PublicKey = group_id
        self.token_lookup: TokenLookup = token_lookup
        self.market_lookup: MarketLookup = market_lookup

        self.ping_interval: int = 10

        # kangda said in Discord: https://discord.com/channels/791995070613159966/836239696467591186/847816026245693451
        # "I think you are better off doing 4,8,16,20,30"
        self.retry_pauses: typing.Sequence[Decimal] = [Decimal(4), Decimal(
            8), Decimal(16), Decimal(20), Decimal(30)]

    @property
    def pool_scheduler(self) -> ThreadPoolScheduler:
        return _pool_scheduler

    def random_client_id(self) -> int:
        # 9223372036854775807 is sys.maxsize for 64-bit systems, with a bit_length of 63.
        # We explicitly want to use a max of 64-bits though, so we use the number instead of
        # sys.maxsize, which could be lower on 32-bit systems or higher on 128-bit systems.
        return random.randrange(9223372036854775807)

    def lookup_group_name(self, group_address: PublicKey) -> str:
        group_address_str = str(group_address)
        for group in MangoConstants["groups"]:
            if group["cluster"] == self.client.cluster and group["publicKey"] == group_address_str:
                return group["name"]

        return "« Unknown Group »"

    def __str__(self) -> str:
        return f"""« 𝙲𝚘𝚗𝚝𝚎𝚡𝚝 '{self.name}':
    Cluster: {self.client.cluster}
    Cluster URL: {self.client.cluster_url}
    Program ID: {self.program_id}
    DEX Program ID: {self.dex_program_id}
    Group Name: {self.group_name}
    Group ID: {self.group_id}
»"""

    def __repr__(self) -> str:
        return f"{self}"
