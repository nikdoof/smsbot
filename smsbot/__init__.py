import logging
import os
import sys
from functools import wraps

from flask import Flask, abort, current_app, request
from telegram.ext import CommandHandler, Updater
from twilio.request_validator import RequestValidator
from waitress import serve

__version__ = '0.0.1'


class TelegramSmsBot(object):

    owner_id = None
    subscriber_ids = []

    def __init__(self, token):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.bot_token = token

    def start(self):
        self.logger.info('Starting bot...')
        self.updater = Updater(self.bot_token, use_context=True)
        self.updater.dispatcher.add_handler(CommandHandler('help', self.help_handler))
        self.updater.dispatcher.add_handler(CommandHandler('start', self.help_handler))
        self.updater.dispatcher.add_handler(CommandHandler('subscribe', self.subscribe_handler))
        self.updater.dispatcher.add_handler(CommandHandler('unsubscribe', self.unsubscribe_handler))
        self.updater.dispatcher.add_error_handler(self.error_handler)

        self.updater.start_polling()
        self.bot = self.updater.bot
        self.logger.info('Bot Ready')

    def stop(self):
        self.updater.stop()

    def help_handler(self, update, context):
        """Send a message when the command /help is issued."""
        self.logger.info('/help command received in chat: %s', update.message.chat)
        update.message.reply_markdown('Smsbot v{0}\n\n/help\n/subscribe\n/unsubscribe'.format(__version__))

    def subscribe_handler(self, update, context):
        self.logger.info('/subscribe command received')
        if not update.message.chat['id'] in self.subscriber_ids:
            self.logger.info('{0} subscribed'.format(update.message.chat['username']))
            self.subscriber_ids.append(update.message.chat['id'])
            update.message.reply_markdown('You have been subscribed to SMS notifications')
        else:
            update.message.reply_markdown('You are already subscribed to SMS notifications')

    def unsubscribe_handler(self, update, context):
        self.logger.info('/unsubscribe command received')
        if update.message.chat['id'] in self.subscriber_ids:
            self.logger.info('{0} unsubscribed'.format(update.message.chat['username']))
            self.subscriber_ids.remove(update.message.chat['id'])
            update.message.reply_markdown('You have been unsubscribed to SMS notifications')
        else:
            update.message.reply_markdown('You are not subscribed to SMS notifications')

    def error_handler(self, update, context):
        """Log Errors caused by Updates."""
        self.logger.warning('Update "%s" caused error "%s"', update, context.error)

    def send_message(self, message, chat_id):
        self.bot.sendMessage(text=message, chat_id=chat_id)

    def send_owner(self, message):
        if self.owner_id:
            self.send_message(message, self.owner_id)

    def send_subscribers(self, message):
        for chat_id in self.subscriber_ids:
            self.send_message(message, chat_id)

    def set_owner(self, chat_id):
        self.owner_id = chat_id

    def add_subscriber(self, chat_id):
        self.subscriber_ids.append(chat_id)


def validate_twilio_request(f):
    """Validates that incoming requests genuinely originated from Twilio"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Create an instance of the RequestValidator class
        twilio_token = os.environ.get('SMSBOT_TWILIO_AUTH_TOKEN')

        if not twilio_token:
            current_app.logger.warning('Twilio request validation skipped due to SMSBOT_TWILIO_AUTH_TOKEN missing')
            return f(*args, **kwargs)

        validator = RequestValidator(twilio_token)

        # Validate the request using its URL, POST data,
        # and X-TWILIO-SIGNATURE header
        request_valid = validator.validate(
            request.url,
            request.form,
            request.headers.get('X-TWILIO-SIGNATURE', ''))

        # Continue processing the request if it's valid, return a 403 error if
        # it's not
        if request_valid or current_app.debug:
            return f(*args, **kwargs)
        else:
            return abort(403)
    return decorated_function


class TwilioWebhookHandler(object):

    def __init__(self):
        self.app = Flask(self.__class__.__name__)
        self.app.add_url_rule('/', 'index', self.index, methods=['GET'])
        self.app.add_url_rule('/message', 'message', self.message, methods=['POST'])
        self.app.add_url_rule('/call', 'call', self.call, methods=['POST'])

    def set_bot(self, bot):
        self.bot = bot

    def index(self):
        return 'Smsbot v{0} - {1}'.format(__version__, request.values.to_dict())

    @validate_twilio_request
    def message(self):

        message = "From: {From}\n\n{Body}".format(**request.values.to_dict())

        current_app.logger.info('Received SMS from {From}: {Body}'.format(**request.values.to_dict()))
        self.bot.send_subscribers(message)

        return '<response></response>'

    @validate_twilio_request
    def call(self):
        current_app.logger.info('Received Call from {From}'.format(**request.values.to_dict()))
        self.bot.send_subscribers('Received Call from {From}, rejecting.'.format(**request.values.to_dict()))
        # Always reject calls
        return '<Response><Reject/></Response>'

    def serve(self, host='0.0.0.0', port=80, debug=False):
        serve(self.app, host=host, port=port)


def main():
    logging.basicConfig(level=logging.INFO)

    listen_host = os.environ.get('SMSBOT_LISTEN_HOST') or '0.0.0.0'
    listen_port = int(os.environ.get('SMSBOT_LISTEN_PORT') or '80')

    token = os.environ.get('SMSBOT_TELEGRAM_BOT_TOKEN')
    if not token:
        logging.exception('Telegram Bot token missing')
        sys.exit(1)

    # Start bot
    telegram_bot = TelegramSmsBot(token)
    telegram_bot.start()

    # Start webhooks
    webhooks = TwilioWebhookHandler()
    webhooks.set_bot(telegram_bot)
    webhooks.serve(host=listen_host, port=listen_port)