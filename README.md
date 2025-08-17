# SMSBot

A simple Telegram bot to receive SMS messages.

Forked from [FiveBoroughs/Twilio2Telegram](https://github.com/FiveBoroughs/Twilio2Telegram).

## Functionality

This simple tool acts as a webhook receiver for the Twilio API, taking messages sent over and posting them on Telegram to a target chat or channel. This is useful for forwarding on 2FA messages, notification text messages for services that don't support international numbers (*cough* Disney, of all people).

The bot is designed to run within a Kubernetes environment, but can be operated as a individual container, or as a hand ran service.

## Configuration

SMSBot can be configured using either a configuration file or environment variables. Environment variables will override any values set in the configuration file.

### Configuration File

Create a configuration file (e.g., `config.ini`) based on the provided `config-example.ini`:

```ini
[logging]
level = INFO

[webhook]
host = 127.0.0.1
port = 80

[telegram]
owner_id = OWNER_USER_ID
bot_token = BOT_TOKEN

[twilio]
account_sid = TWILIO_ACCOUNT_SID
auth_token = TWILIO_AUTH_TOKEN
```

### Environment Variables

All configuration options can be overridden using environment variables:

| Environment Variable        | Config Section | Config Key  | Required? | Description                                                                 |
| --------------------------- | -------------- | ----------- | --------- | --------------------------------------------------------------------------- |
| SMSBOT_LOGGING_LEVEL        | logging        | level       | No        | The log level to output to the console, defaults to `INFO`                  |
| SMSBOT_TELEGRAM_BOT_TOKEN   | telegram       | bot_token   | Yes       | Your Bot Token for Telegram                                                 |
| SMSBOT_TELEGRAM_OWNER_ID    | telegram       | owner_id    | No        | ID of the owner of this bot                                                 |
| SMSBOT_TELEGRAM_SUBSCRIBERS | telegram       | subscribers | No        | A list of IDs, separated by commas, to add to the subscribers list on start |
| SMSBOT_TWILIO_ACCOUNT_SID   | twilio         | account_sid | No        | Twilio account SID                                                          |
| SMSBOT_TWILIO_AUTH_TOKEN    | twilio         | auth_token  | No        | Twilio auth token, used to validate any incoming webhook calls              |
| SMSBOT_WEBHOOK_HOST         | webhook        | host        | No        | The host for the webhooks to listen on, defaults to `127.0.0.1`             |
| SMSBOT_WEBHOOK_PORT         | webhook        | port        | No        | The port to listen to, defaults to `80`                                     |

## Setup

To configure SMSBot, you'll need a Twilio account, either paid or trial is fine.

1. Copy `config-example.ini` to `config.ini` and update the values, or set the appropriate environment variables.
2. Setup a number in the location you want.
3. Under Phone Numbers -> Manage -> Active Numbers, click the number you want to setup.
4. In the "Voice & Fax" section, update the "A Call Comes In" to the URL of your SMSBot instance, with the endpoint being `/call`, e.g. `http://mymachine.test.com/call`
5. In the "Messaging" section, update the "A Message Comes In" to the URL of your SMSBot instance, with the endpoint being `/message`, e.g. `http://mymachine.test.com/message`

Your bot should now receive messages, on Telegram you need to start a chat or invite it into any channels you want, then update the `SMSBOT_TELEGRAM_SUBSCRIBERS` values with their IDs.

**Note**: You cannot send test messages from your Twilio account to your Twilio numbers, they'll be silently dropped or fail with an "Invalid Number" error.

## Helm Chart

Previously this repository had a Helm chart to configure smsbot for Kubernetes clusters. It was removed as the chart itself didn't offer any additional functionality outside of creating the deployment by hand. If you want to use Helm then I suggest using one of the following generic charts that can be used to deploy applications:

* https://github.com/stakater/application
* https://github.com/nikdoof/helm-charts/tree/master/charts/common-chart
