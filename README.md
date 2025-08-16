# SMSBot

A simple Telegram bot to receive SMS messages.

Forked from [FiveBoroughs/Twilio2Telegram](https://github.com/FiveBoroughs/Twilio2Telegram).

## Functionality

This simple tool acts as a webhook receiver for the Twilio API, taking messages sent over and posting them on Telegram to a target chat or channel. This is useful for forwarding on 2FA messages, notification text messages for services that don't support international numbers (*cough* Disney, of all people).

The bot is designed to run within a Kubernetes environment, but can be operated as a individual container, or as a hand ran service.

## Configuration

All configuration is provided via environment variables

| Variable                   | Required? | Description                                                                 |
| -------------------------- | --------- | --------------------------------------------------------------------------- |
| SMSBOT_DEFAULT_SUBSCRIBERS | No        | A list of IDs, seperated by commas, to add to the subscribers list on start |
| SMSBOT_LISTEN_HOST         | No        | The host for the webhooks to listen on, defaults to `0.0.0.0`               |
| SMSBOT_LISTEN_PORT         | No        | The port to listen to, defaults to `80`                                     |
| SMSBOT_OWNER_ID            | No        | ID of the owner of this bot                                                 |
| SMSBOT_TELEGRAM_BOT_TOKEN  | Yes       | Your Bot Token for Telegram                                                 |
| SMSBOT_TWILIO_AUTH_TOKEN   | No        | Twilio auth token, used to validate any incoming webhook calls              |

## Setup

To configure SMSBot, you'll need a Twilio account, either paid or trial is fine.

* Setup a number in the location you want.
* Under Phone Numbers -> Manage -> Active Numbers, click the number you want to setup.
* In the "Voice & Fax" section, update the "A Call Comes In" to the URL of your SMSBot instance, with the endpoint being `/call`, e.g. `http://mymachine.test.com/call`
* In the "Messaging" section, update the "A Message Comes In" to the URL of your SMSBot instance, with the endpoint being `/message`, e.g. `http://mymachine.test.com/message`

Your bot should now receive messages, on Telegram you need to start a chat or invite it into any channels you want, then update the `SMSBOT_DEFAULT_SUBSCRIBERS` values with their IDs.

**Note**: You cannot send test messages from your Twilio account to your Twilio numbers, they'll be silently dropped or fail with an "Invalid Number" error.

## Helm Chart

Previously this repository had a Helm chart to configure smsbot for Kubernetes clusters. It was removed as the chart itself didn't offer any additional functionality outside of creating the deployment by hand. If you want to use Helm then I suggest using one of the following generic charts that can be used to deploy applications:

* https://github.com/stakater/application
* https://github.com/nikdoof/helm-charts/tree/master/charts/common-chart
