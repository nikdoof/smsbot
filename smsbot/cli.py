import logging
import os
import sys

import pkg_resources

from smsbot.telegram import TelegramSmsBot
from smsbot.webhook_handler import TwilioWebhookHandler

pkg_version = pkg_resources.require('smsbot')[0].version


def main():
    logging.basicConfig(level=logging.INFO)
    logging.info('smsbot v%s', pkg_version)

    listen_host = os.environ.get('SMSBOT_LISTEN_HOST') or '0.0.0.0'
    listen_port = int(os.environ.get('SMSBOT_LISTEN_PORT') or '80')

    token = os.environ.get('SMSBOT_TELEGRAM_BOT_TOKEN')
    if not token:
        logging.error('Telegram Bot token missing')
        sys.exit(1)

    # Start bot
    telegram_bot = TelegramSmsBot(token)

    # Set the owner ID if configured
    if 'SMSBOT_OWNER_ID' in os.environ:
        telegram_bot.set_owner(os.environ.get('SMSBOT_OWNER_ID'))
    else:
        logging.warning('No Owner ID is set, which is not a good idea...')

    # Add default subscribers
    if 'SMSBOT_DEFAULT_SUBSCRIBERS' in os.environ:
        for chat_id in os.environ.get('SMSBOT_DEFAULT_SUBSCRIBERS').split(','):
            telegram_bot.add_subscriber(chat_id)

    telegram_bot.start()

    # Start webhooks
    webhooks = TwilioWebhookHandler()
    webhooks.set_bot(telegram_bot)
    webhooks.serve(host=listen_host, port=listen_port)
