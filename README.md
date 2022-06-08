# SMSBot

A simple Telegram bot to receive SMS messages.

Forked from [FiveBoroughs/Twilio2Telegram](https://github.com/FiveBoroughs/Twilio2Telegram).

## Functionality

This simple tool acts as a webhook receiver for the Twilio API, taking messages sent over and posting them on Telegram to a target chat or channel. This is useful for forwarding on 2FA messages, notification text messages for services that don't support international numbers (*cough* Disney, of all people).

The bot is designed to run within a Kubernetes environment, but can be operated as a individual container, or as a hand ran service.