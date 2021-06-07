from .context import mango
from .fakes import fake_account_info, fake_seeded_public_key

from datetime import datetime, timedelta
from decimal import Decimal
from solana.publickey import PublicKey


def test_aggregator_config_constructor():
    description: str = "Test Aggregator Config"
    decimals: Decimal = Decimal(5)
    restart_delay: Decimal = Decimal(30)
    max_submissions: Decimal = Decimal(10)
    min_submissions: Decimal = Decimal(2)
    reward_amount: Decimal = Decimal(30)
    reward_token_account: PublicKey = fake_seeded_public_key("reward token account")
    actual = mango.AggregatorConfig(mango.Version.V1, description, decimals, restart_delay,
                                    max_submissions, min_submissions, reward_amount, reward_token_account)
    assert actual is not None
    assert actual.logger is not None
    assert actual.version == mango.Version.V1
    assert actual.description == description
    assert actual.decimals == decimals
    assert actual.restart_delay == restart_delay
    assert actual.max_submissions == max_submissions
    assert actual.min_submissions == min_submissions
    assert actual.reward_amount == reward_amount
    assert actual.reward_token_account == reward_token_account


def test_round_constructor():
    id: Decimal = Decimal(85)
    updated_at: datetime = datetime.now()
    created_at: datetime = updated_at - timedelta(minutes=5)
    actual = mango.Round(mango.Version.V1, id, created_at, updated_at)
    assert actual is not None
    assert actual.logger is not None
    assert actual.version == mango.Version.V1
    assert actual.id == id
    assert actual.created_at == created_at
    assert actual.updated_at == updated_at

    # def __init__(self, version: Version, round_id: Decimal, median: Decimal, created_at: datetime.datetime, updated_at: datetime.datetime):


def test_answer_constructor():
    round_id: Decimal = Decimal(85)
    median: Decimal = Decimal(25)
    updated_at: datetime = datetime.now()
    created_at: datetime = updated_at - timedelta(minutes=5)
    actual = mango.Answer(mango.Version.V1, round_id, median, created_at, updated_at)
    assert actual is not None
    assert actual.logger is not None
    assert actual.version == mango.Version.V1
    assert actual.round_id == round_id
    assert actual.median == median
    assert actual.created_at == created_at
    assert actual.updated_at == updated_at


def test_aggregator_constructor():
    account_info = fake_account_info()
    description: str = "Test Aggregator Config"
    decimals: Decimal = Decimal(5)
    restart_delay: Decimal = Decimal(30)
    max_submissions: Decimal = Decimal(10)
    min_submissions: Decimal = Decimal(2)
    reward_amount: Decimal = Decimal(30)
    reward_token_account: PublicKey = fake_seeded_public_key("reward token account")
    config = mango.AggregatorConfig(mango.Version.V1, description, decimals, restart_delay,
                                    max_submissions, min_submissions, reward_amount, reward_token_account)
    initialized = True
    name = "Test Aggregator"
    owner = fake_seeded_public_key("owner")

    id: Decimal = Decimal(85)
    updated_at: datetime = datetime.now()
    created_at: datetime = updated_at - timedelta(minutes=5)
    round = mango.Round(mango.Version.V1, id, created_at, updated_at)

    round_submissions = fake_seeded_public_key("round submissions")

    round_id: Decimal = Decimal(85)
    median: Decimal = Decimal(25)
    answer = mango.Answer(mango.Version.V1, round_id, median, created_at, updated_at)

    answer_submissions = fake_seeded_public_key("answer submissions")

    actual = mango.Aggregator(account_info, mango.Version.V1, config, initialized,
                              name, owner, round, round_submissions, answer, answer_submissions)
    assert actual is not None
    assert actual.logger is not None
    assert actual.account_info == account_info
    assert actual.version == mango.Version.V1
    assert actual.config == config
    assert actual.initialized == initialized
    assert actual.name == name
    assert actual.owner == owner
    assert actual.round == round
    assert actual.round_submissions == round_submissions
    assert actual.answer == answer
    assert actual.answer_submissions == answer_submissions
