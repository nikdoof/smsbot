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
