from .context import mango

import typing


class MockNotificationTarget(mango.NotificationTarget):
    def __init__(self):
        super().__init__()
        self.send_notification_called = False

    def send_notification(self, item: typing.Any) -> None:
        self.send_notification_called = True


def test_notification_target_constructor():
    succeeded = False
    try:
        mango.AccountLiquidator()
    except TypeError:
        # Can't instantiate the abstract base class.
        succeeded = True
    assert succeeded


def test_telegram_notification_target_constructor():
    address = "chat@bot"
    actual = mango.TelegramNotificationTarget(address)
    assert actual is not None
    assert actual.logger is not None
    assert actual.chat_id == "chat"
    assert actual.bot_id == "bot"


def test_discord_notification_target_constructor():
    address = "discord-address"
    actual = mango.DiscordNotificationTarget(address)
    assert actual is not None
    assert actual.logger is not None
    assert actual.address == address


def test_mailjet_notification_target_constructor():
    encoded_parameters = "user:secret:subject:from%20name:from@address:to%20name%20with%20colon%3A:to@address"
    actual = mango.MailjetNotificationTarget(encoded_parameters)
    assert actual is not None
    assert actual.logger is not None
    assert actual.api_key == "user"
    assert actual.api_secret == "secret"
    assert actual.subject == "subject"
    assert actual.from_name == "from name"
    assert actual.from_address == "from@address"
    assert actual.to_name == "to name with colon:"
    assert actual.to_address == "to@address"


def test_csvfile_notification_target_constructor():
    filename = "test-filename"
    actual = mango.CsvFileNotificationTarget(filename)
    assert actual is not None
    assert actual.logger is not None
    assert actual.filename == filename


def test_filtering_notification_target_constructor():
    mock = MockNotificationTarget()

    def func(_):
        return True
    actual = mango.FilteringNotificationTarget(mock, func)
    assert actual is not None
    assert actual.logger is not None
    assert actual.inner_notifier == mock
    assert actual.filter_func == func


def test_filtering_notification_target():
    mock = MockNotificationTarget()
    filtering = mango.FilteringNotificationTarget(mock, lambda x: x == "yes")
    filtering.send("no")
    assert(not mock.send_notification_called)
    filtering.send("yes")
    assert(mock.send_notification_called)


def test_parse_subscription_target():
    telegram_target = mango.parse_subscription_target(
        "telegram:012345678@9876543210:ABCDEFGHijklmnop-qrstuvwxyzABCDEFGH")
    assert telegram_target is not None

    discord_target = mango.parse_subscription_target(
        "discord:https://discord.com/api/webhooks/012345678901234567/ABCDE_fghij-KLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN")
    assert discord_target is not None

    mailjet_target = mango.parse_subscription_target(
        "mailjet:user:secret:subject:from%20name:from@address:to%20name%20with%20colon%3A:to@address")
    assert mailjet_target is not None

    csvfile_target = mango.parse_subscription_target("csvfile:filename.csv")
    assert csvfile_target is not None
