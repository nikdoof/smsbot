import argparse
import logging
import os

from smsbot.telegram import TelegramSmsBot
from smsbot.webhook_handler import TwilioWebhookHandler
from smsbot.utils import get_smsbot_version


def main():
    parser = argparse.ArgumentParser('smsbot')
    parser.add_argument('--listen-host', default=os.environ.get('SMSBOT_LISTEN_HOST') or '0.0.0.0')
    parser.add_argument('--listen-port', default=os.environ.get('SMSBOT_LISTEN_PORT') or '80')
    parser.add_argument('--telegram-bot-token', default=os.environ.get('SMSBOT_TELEGRAM_BOT_TOKEN'))
    parser.add_argument('--owner-id', default=os.environ.get('SMSBOT_OWNER_ID'))
    parser.add_argument('--default-subscribers', default=os.environ.get('SMSBOT_DEFAULT_SUBSCRIBERS'))
    parser.add_argument('--log-level', default='INFO')
    args = parser.parse_args()

    logging.basicConfig(level=logging.getLevelName(args.log_level))
    logging.info('smsbot v%s', get_smsbot_version())
    logging.debug('Arguments: %s', args)

    # Start bot
    telegram_bot = TelegramSmsBot(args.telegram_bot_token)

    # Set the owner ID if configured
    if args.owner_id:
        telegram_bot.set_owner(args.owner_id)
    else:
        logging.warning('No Owner ID is set, which is not a good idea...')

    # Add default subscribers
    if args.default_subscribers:
        for chat_id in args.default_subscribers.split(','):
            telegram_bot.add_subscriber(chat_id)

    telegram_bot.start()

    # Start webhooks
    webhooks = TwilioWebhookHandler()
    webhooks.set_bot(telegram_bot)
    webhooks.serve(host=args.listen_host, port=args.listen_port)
