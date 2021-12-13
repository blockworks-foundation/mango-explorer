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


import abc
import csv
import logging
import os.path
import requests
import typing

from urllib.parse import unquote

from .liquidationevent import LiquidationEvent


# # 🥭 Notification
#
# This file contains code to send arbitrary notifications.
#

# # 🥭 NotificationTarget class
#
# This base class is the root of the different notification mechanisms.
#
# Derived classes should override `send_notification()` to implement their own sending logic.
#
# Derived classes should not override `send()` since that is the interface outside classes call and it's used to ensure `NotificationTarget`s don't throw an exception when sending.
#
class NotificationTarget(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    def send(self, item: typing.Any) -> None:
        try:
            self.send_notification(item)
        except Exception as exception:
            self._logger.error(f"Error sending {item} - {self} - {exception}")

    @abc.abstractmethod
    def send_notification(self, item: typing.Any) -> None:
        raise NotImplementedError("NotificationTarget.send() is not implemented on the base type.")

    def __str__(self) -> str:
        return "« NotificationTarget »"

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 TelegramNotificationTarget class
#
# The `TelegramNotificationTarget` sends messages to Telegram.
#
# The format for the telegram notification is:
# 1. The word 'telegram'
# 2. A colon ':'
# 3. The chat ID
# 4. An '@' symbol
# 5. The bot token
#
# For example:
# ```
# telegram:<CHAT-ID>@<BOT-TOKEN>
# ```
#
# The [Telegram instructions to create a bot](https://core.telegram.org/bots#creating-a-new-bot)
# show you how to create the bot token.
class TelegramNotificationTarget(NotificationTarget):
    def __init__(self, address: str) -> None:
        super().__init__()
        chat_id, bot_id = address.split("@", 1)
        self.chat_id = chat_id
        self.bot_id = bot_id

    def send_notification(self, item: typing.Any) -> None:
        payload = {"disable_notification": True, "chat_id": self.chat_id, "text": str(item)}
        url = f"https://api.telegram.org/bot{self.bot_id}/sendMessage"
        headers = {"Content-Type": "application/json"}
        requests.post(url, json=payload, headers=headers)

    def __str__(self) -> str:
        return f"« TelegramNotificationTarget Chat ID: {self.chat_id} »"


# # 🥭 DiscordNotificationTarget class
#
# The `DiscordNotificationTarget` sends messages to Discord.
#
class DiscordNotificationTarget(NotificationTarget):
    def __init__(self, address: str) -> None:
        super().__init__()
        self.address = address

    def send_notification(self, item: typing.Any) -> None:
        payload = {
            "content": str(item)
        }
        url = self.address
        headers = {"Content-Type": "application/json"}
        requests.post(url, json=payload, headers=headers)

    def __str__(self) -> str:
        return f"« DiscordNotificationTarget Address: {self.address} »"


# # 🥭 MailjetNotificationTarget class
#
# The `MailjetNotificationTarget` sends an email through [Mailjet](https://mailjet.com).
#
# In order to pass everything in to the notifier as a single string (needed to stop
# command-line parameters form getting messy), `MailjetNotificationTarget` requires a
# compound string, separated by colons.
# ```
# mailjet:<MAILJET-API-KEY>:<MAILJET-API-SECRET>:FROM-NAME:FROM-ADDRESS:TO-NAME:TO-ADDRESS
#
# ```
# Individual components are URL-encoded (so, for example, spaces are replaces with %20,
# colons are replaced with %3A).
#
# * `<MAILJET-API-KEY>` and `<MAILJET-API-SECRET>` are from your [Mailjet](https://mailjet.com) account.
# * `FROM-NAME` and `TO-NAME` are just text fields that are used as descriptors in the email messages.
# * `FROM-ADDRESS` is the address the email appears to come from. This must be validated with [Mailjet](https://mailjet.com).
# * `TO-ADDRESS` is the destination address - the email account to which the email is being sent.
#
# Mailjet provides a client library, but really we don't need or want more dependencies. This`
# code just replicates the `curl` way of doing things:
# ```
# curl -s \
# 	-X POST \
# 	--user "$MJ_APIKEY_PUBLIC:$MJ_APIKEY_PRIVATE" \
# 	https://api.mailjet.com/v3.1/send \
# 	-H 'Content-Type: application/json' \
# 	-d '{
#       "SandboxMode":"true",
#       "Messages":[
#         {
#           "From":[
#             {
#               "Email":"pilot@mailjet.com",
#               "Name":"Your Mailjet Pilot"
#             }
#           ],
#           "HTMLPart":"<h3>Dear passenger, welcome to Mailjet!</h3><br />May the delivery force be with you!",
#           "Subject":"Your email flight plan!",
#           "TextPart":"Dear passenger, welcome to Mailjet! May the delivery force be with you!",
#           "To":[
#             {
#               "Email":"passenger@mailjet.com",
#               "Name":"Passenger 1"
#             }
#           ]
#         }
#       ]
# 	}'
# ```
class MailjetNotificationTarget(NotificationTarget):
    def __init__(self, encoded_parameters: str) -> None:
        super().__init__()
        self.address = "https://api.mailjet.com/v3.1/send"
        api_key, api_secret, subject, from_name, from_address, to_name, to_address = encoded_parameters.split(":")
        self.api_key: str = unquote(api_key)
        self.api_secret: str = unquote(api_secret)
        self.subject: str = unquote(subject)
        self.from_name: str = unquote(from_name)
        self.from_address: str = unquote(from_address)
        self.to_name: str = unquote(to_name)
        self.to_address: str = unquote(to_address)

    def send_notification(self, item: typing.Any) -> None:
        payload = {
            "Messages": [
                {
                    "From": {
                        "Email": self.from_address,
                        "Name": self.from_name
                    },
                    "Subject": self.subject,
                    "TextPart": str(item),
                    "To": [
                        {
                            "Email": self.to_address,
                            "Name": self.to_name
                        }
                    ]
                }
            ]
        }

        url = self.address
        headers = {"Content-Type": "application/json"}
        requests.post(url, json=payload, headers=headers, auth=(self.api_key, self.api_secret))

    def __str__(self) -> str:
        return f"« MailjetNotificationTarget To: '{self.to_name}' '{self.to_address}' with subject '{self.subject}' »"


# # 🥭 CsvFileNotificationTarget class
#
# Outputs a liquidation event to CSV. Nothing is written if the item is not a
# `LiquidationEvent`.
#
# Headers for the CSV file should be:
# ```
# "Timestamp","Liquidator Name","Group","Succeeded","Signature","Wallet","Margin Account","Token Changes"
# ```
# Token changes are listed as pairs of value plus symbol, so each token change adds two
# columns to the output. Token changes may arrive in different orders, so ordering of token
# changes is not guaranteed to be consistent from transaction to transaction.
#
class CsvFileNotificationTarget(NotificationTarget):
    def __init__(self, filename: str) -> None:
        super().__init__()
        self.filename = filename

    def send_notification(self, item: typing.Any) -> None:
        if isinstance(item, LiquidationEvent):
            event: LiquidationEvent = item
            if not os.path.isfile(self.filename) or os.path.getsize(self.filename) == 0:
                with open(self.filename, "w") as empty_file:
                    empty_file.write(
                        '"Timestamp","Liquidator Name","Group","Succeeded","Signature","Wallet","Margin Account","Token Changes"\n')

            with open(self.filename, "a") as csvfile:
                result = "Succeeded" if event.succeeded else "Failed"
                row_data = [event.timestamp, event.liquidator_name, event.group_name, result,
                            " ".join(event.signatures), event.wallet_address, event.account_address]
                for change in event.changes:
                    row_data += [f"{change.value:.8f}", change.token.name]
                file_writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
                file_writer.writerow(row_data)

    def __str__(self) -> str:
        return f"« CsvFileNotificationTarget File: {self.filename} »"


# # 🥭 FilteringNotificationTarget class
#
# This class takes a `NotificationTarget` and a filter function, and only calls the
# `NotificationTarget` if the filter function returns `True` for the notification item.
#
class FilteringNotificationTarget(NotificationTarget):
    def __init__(self, inner_notifier: NotificationTarget, filter_func: typing.Callable[[typing.Any], bool]) -> None:
        super().__init__()
        self.inner_notifier: NotificationTarget = inner_notifier
        self.filter_func = filter_func

    def send_notification(self, item: typing.Any) -> None:
        if self.filter_func(item):
            self.inner_notifier.send_notification(item)

    def __str__(self) -> str:
        return f"« FilteringNotificationTarget For: {self.inner_notifier} »"


# # 🥭 ConsoleNotificationTarget class
#
# The `ConsoleNotificationTarget` prints messages on the console.
#
class ConsoleNotificationTarget(NotificationTarget):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name

    def send_notification(self, item: typing.Any) -> None:
        print(self.name, item)

    def __str__(self) -> str:
        return f"« ConsoleNotificationTarget '{self.name}' »"


# # 🥭 CompoundNotificationTarget class
#
# The `CompoundNotificationTarget` acts as a single `NotificationTarget`, sending notifications to all
# inner `NotificationTarget`s.
#
class CompoundNotificationTarget(NotificationTarget):
    def __init__(self, targets: typing.Sequence[NotificationTarget]) -> None:
        super().__init__()
        self.targets: typing.Sequence[NotificationTarget] = targets
        self.in_exception_handler: bool = False

    def send_notification(self, item: typing.Any) -> None:
        for target in self.targets:
            try:
                target.send(item)
            except Exception as exception:
                if not self.in_exception_handler:
                    self.in_exception_handler = True
                    self._logger.error(f"Failed to send notification to: {target} - {exception}")
            finally:
                self.in_exception_handler = False

    def __str__(self) -> str:
        inner: typing.List[str] = []
        for target in self.targets:
            inner += [f"{target}"]
        inner_text: str = "\n    ".join(inner)
        return f"""« CompoundNotificationTarget with {len(self.targets)} inner targets:
    {inner_text}
»"""


# # 🥭 parse_notification_target() function
#
# `parse_notification_target()` takes a parameter as a string and returns a notification
# target.
#
# This is most likely used when parsing command-line arguments - this function can be used
# in the `type` parameter of an `add_argument()` call.
#
def parse_notification_target(target: str) -> NotificationTarget:
    protocol, destination = target.split(":", 1)

    if protocol == "telegram":
        return TelegramNotificationTarget(destination)
    elif protocol == "discord":
        return DiscordNotificationTarget(destination)
    elif protocol == "mailjet":
        return MailjetNotificationTarget(destination)
    elif protocol == "csvfile":
        return CsvFileNotificationTarget(destination)
    elif protocol == "console":
        return ConsoleNotificationTarget(destination)
    else:
        raise Exception(f"Unknown protocol: {protocol}")


# # 🥭 NotificationHandler class
#
# A bridge between the worlds of notifications and logging. This allows any
# `NotificationTarget` to be plugged in to the `logging` subsystem to receive log messages
# and notify however it chooses.
#
class NotificationHandler(logging.StreamHandler):
    def __init__(self, target: NotificationTarget) -> None:
        logging.StreamHandler.__init__(self)
        self.target = target

    def emit(self, record: logging.LogRecord) -> None:
        # Don't send error logging from solanaweb3
        if record.name == "solanaweb3.rpc.httprpc.HTTPClient":
            return
        message = self.format(record)
        self.target.send_notification(message)

    def __str__(self) -> str:
        return "« NotificationHandler »"
