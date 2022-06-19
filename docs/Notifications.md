# 🥭 Mango Explorer

# 🛎️ Notifications

Sometimes you want to be notified when something happens. For instance, you might want to get an alert when your `liquidator` successfully performs a liquidation.

🥭 Mango Explorer has a consistent approach to notifications across its commands, allowing you to send notifications to:
* Telegram
* Discord
* Mailjet
* CSV files

Configuring all of these 'notification targets' in a command-line could be tricky, so:

> Each notification target parameter starts with a handler name, a colon, and then handler-specific configuration.

For example, to record liquidations to a CSV file `/var/mango-explorer/liquidations.csv`, you'd pass the following additional parameters to your `liquidator`:
```
--notify-successful-liquidations csvfile:/var/mango-explorer/liquidations.csv
```

Available notifications varies by program (you can always use the `--help` parameter to see what parameters a given command accepts), but here are the possible notification parameters for the `liquidator` command:
* --notify-liquidations
* --notify-successful-liquidations
* --notify-failed-liquidations
* --notify-errors

# 💌 Telegram

The `TelegramNotificationTarget` sends messages to [Telegram](https://telegram.org/).

The format for configuring the telegram notification is:
1. The word 'telegram'
2. A colon ':'
3. The chat ID
4. An '@' symbol
5. The bot token

So:
telegram:<CHAT-ID>@<BOT-TOKEN>

For example:
```
telegram:012345678@9876543210:ABCDEFGHijklmnop-qrstuvwxyzABCDEFGH
```

The [Telegram instructions to create a bot](https://core.telegram.org/bots#creating-a-new-bot) show you how to create the bot token.

# 💬 Discord

The `DiscordNotificationTarget` sends messages to [Discord](https://discord.com/).

The format for configuring the discord notification target is:
1. The word 'discord'
2. A colon ':'
3. The Discord webhook URL for the channel you want to show the notifications.

So:
discord:<DISCORD-WEBHOOK_URL>

For example:
```
discord:https://discord.com/api/webhooks/012345678901234567/ABCDE_fghij-KLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN
```

These [Discord instructions](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) show you how to create a webhook.


# 📧 Mailjet

The `MailjetNotificationTarget` sends an email through [Mailjet](https://mailjet.com).

This is the most complicated configuration, because it involves so many different parameters.

In order to pass everything in to the notifier as a single string (needed to stop command-line parameters form getting messy), `MailjetNotificationTarget` requires a long compound string, separated by colons.

The format for configuring the mailjet notification is:
1. The word 'mailjet'
2. A colon ':'
3. The chat ID
4. An '@' symbol
5. The bot token

So:
mailjet:<MAILJET-API-KEY>:<MAILJET-API-SECRET>:FROM-NAME:FROM-ADDRESS:TO-NAME:TO-ADDRESS

For example:
```
mailjet:user:secret:subject:from%20name:from@address:to%20name%20with%20colon%3A:to@address
```

Individual components are URL-encoded (so, for example, spaces are replaces with %20,
colons are replaced with %3A).
* `<MAILJET-API-KEY>` and `<MAILJET-API-SECRET>` are from your [Mailjet](https://mailjet.com) count.
* `FROM-NAME` and `TO-NAME` are just text fields that are used as descriptors in the email messages.
* `FROM-ADDRESS` is the address the email appears to come from. This must be validated with ailjet](https://mailjet.com).
* `TO-ADDRESS` is the destination address - the email account to which the email is being sent.
Mailjet provides a client library, but really we don't need or want more dependencies.
