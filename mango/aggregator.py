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


import datetime
import logging
import typing

from decimal import Decimal
from solana.publickey import PublicKey

from .accountinfo import AccountInfo
from .addressableaccount import AddressableAccount
from .context import Context
from .layouts import layouts
from .version import Version


# # 🥭 AggregatorConfig class
#

class AggregatorConfig:
    def __init__(self, version: Version, description: str, decimals: Decimal, restart_delay: Decimal,
                 max_submissions: Decimal, min_submissions: Decimal, reward_amount: Decimal,
                 reward_token_account: PublicKey):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.version: Version = version
        self.description: str = description
        self.decimals: Decimal = decimals
        self.restart_delay: Decimal = restart_delay
        self.max_submissions: Decimal = max_submissions
        self.min_submissions: Decimal = min_submissions
        self.reward_amount: Decimal = reward_amount
        self.reward_token_account: PublicKey = reward_token_account

    @staticmethod
    def from_layout(layout: typing.Any) -> "AggregatorConfig":
        return AggregatorConfig(Version.UNSPECIFIED, layout.description, layout.decimals,
                                layout.restart_delay, layout.max_submissions, layout.min_submissions,
                                layout.reward_amount, layout.reward_token_account)

    def __str__(self) -> str:
        return f"« AggregatorConfig: '{self.description}', Decimals: {self.decimals} [restart delay: {self.restart_delay}], Max: {self.max_submissions}, Min: {self.min_submissions}, Reward: {self.reward_amount}, Reward Account: {self.reward_token_account} »"

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 Round class
#


class Round:
    def __init__(self, version: Version, id: Decimal, created_at: datetime.datetime, updated_at: datetime.datetime):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.version: Version = version
        self.id: Decimal = id
        self.created_at: datetime.datetime = created_at
        self.updated_at: datetime.datetime = updated_at

    @staticmethod
    def from_layout(layout: typing.Any) -> "Round":
        return Round(Version.UNSPECIFIED, layout.id, layout.created_at, layout.updated_at)

    def __str__(self) -> str:
        return f"« Round[{self.id}], Created: {self.updated_at}, Updated: {self.updated_at} »"

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 Answer class
#

class Answer:
    def __init__(self, version: Version, round_id: Decimal, median: Decimal, created_at: datetime.datetime, updated_at: datetime.datetime):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.version: Version = version
        self.round_id: Decimal = round_id
        self.median: Decimal = median
        self.created_at: datetime.datetime = created_at
        self.updated_at: datetime.datetime = updated_at

    @staticmethod
    def from_layout(layout: typing.Any) -> "Answer":
        return Answer(Version.UNSPECIFIED, layout.round_id, layout.median, layout.created_at, layout.updated_at)

    def __str__(self) -> str:
        return f"« Answer: Round[{self.round_id}], Median: {self.median:,.8f}, Created: {self.updated_at}, Updated: {self.updated_at} »"

    def __repr__(self) -> str:
        return f"{self}"

# # 🥭 Aggregator class
#


class Aggregator(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version, config: AggregatorConfig,
                 initialized: bool, name: str, owner: PublicKey, round_: Round,
                 round_submissions: PublicKey, answer: Answer, answer_submissions: PublicKey):
        super().__init__(account_info)
        self.version: Version = version
        self.config: AggregatorConfig = config
        self.initialized: bool = initialized
        self.name: str = name
        self.owner: PublicKey = owner
        self.round: Round = round_
        self.round_submissions: PublicKey = round_submissions
        self.answer: Answer = answer
        self.answer_submissions: PublicKey = answer_submissions

    @property
    def price(self) -> Decimal:
        return self.answer.median / (10 ** self.config.decimals)

    @staticmethod
    def from_layout(layout: typing.Any, account_info: AccountInfo, name: str) -> "Aggregator":
        config = AggregatorConfig.from_layout(layout.config)
        initialized = bool(layout.initialized)
        round_ = Round.from_layout(layout.round)
        answer = Answer.from_layout(layout.answer)

        return Aggregator(account_info, Version.UNSPECIFIED, config, initialized, name, layout.owner,
                          round_, layout.round_submissions, answer, layout.answer_submissions)

    @staticmethod
    def parse(context: Context, account_info: AccountInfo) -> "Aggregator":
        data = account_info.data
        if len(data) != layouts.AGGREGATOR.sizeof():
            raise Exception(f"Data length ({len(data)}) does not match expected size ({layouts.AGGREGATOR.sizeof()})")

        name = context.lookup_oracle_name(account_info.address)
        layout = layouts.AGGREGATOR.parse(data)
        return Aggregator.from_layout(layout, account_info, name)

    @staticmethod
    def load(context: Context, account_address: PublicKey):
        account_info = AccountInfo.load(context, account_address)
        if account_info is None:
            raise Exception(f"Aggregator account not found at address '{account_address}'")
        return Aggregator.parse(context, account_info)

    def __str__(self) -> str:
        return f"""
« Aggregator '{self.name}' [{self.version}]:
    Config: {self.config}
    Initialized: {self.initialized}
    Owner: {self.owner}
    Round: {self.round}
    Round Submissions: {self.round_submissions}
    Answer: {self.answer}
    Answer Submissions: {self.answer_submissions}
»
"""
