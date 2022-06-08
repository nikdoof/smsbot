try:
    import os
    import logging
    from functools import wraps
    from flask import Flask, request, abort
    from waitress import serve
    from twilio.request_validator import RequestValidator
    from telegram import ParseMode
    from telegram.ext import Updater, CommandHandler
except ImportError as err:
    print(f"Failed to import required modules: {err}")

# FB - Enable logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

webhook_listener = Flask(__name__)


def validate_twilio_request(f):
    """Validates that incoming requests genuinely originated from Twilio"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # FB - Create an instance of the RequestValidator class
        validator = RequestValidator(os.environ.get('TWILIO_AUTH_TOKEN'))

        # FB - Validate the request using its URL, POST data, and X-TWILIO-SIGNATURE header
        request_valid = validator.validate(
            request.url,
            request.form,
            request.headers.get('X-TWILIO-SIGNATURE', ''))

        # FB - Continue processing the request if it's valid, return a 403 error if it's not
        if request_valid:
            return f(*args, **kwargs)
        else:
            logger.error('Invalid twilio request, aborting')
            return abort(403)
    return decorated_function


def tg_help_handler(update, context):
    """Send a message when the command /help is issued."""
    logger.info('/help command received in chat: %s', update.message.chat)
    update.message.reply_markdown(
        'Find out more on [Github](https://github.com/FiveBoroughs/Twilio2Telegram)')


def tg_error_handler(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def tg_bot_start():
    """Start the telegram bot."""
    # FB - Create the Updater
    updater = Updater(os.environ.get('TELEGRAM_BOT_TOKEN'), use_context=True)

    # FB - Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # FB - on /help command
    dispatcher.add_handler(CommandHandler("help", tg_help_handler))

    # FB - log all errors
    dispatcher.add_error_handler(tg_error_handler)

    # FB - Start the Bot
    updater.start_polling()

    return updater.bot


def tg_send_owner_message(message):
    """Send telegram message to owner."""
    telegram_bot.sendMessage(text=message, chat_id=os.environ.get('TELEGRAM_OWNER'), parse_mode=ParseMode.MARKDOWN)


def tg_send_subscribers_message(message):
    """Send telegram messages to subscribers."""
    for telegram_destination in os.environ.get('TELEGRAM_SUBSCRIBERS').split(','):
        telegram_bot.sendMessage(
            text=message, chat_id=telegram_destination, parse_mode=ParseMode.MARKDOWN)


@webhook_listener.route('/', methods=['GET'])
def index():
    """Upon call of homepage."""
    logger.info('"/" reached, IP: %s', request.remote_addr)

    return webhook_listener.send_static_file('Index.html')


@webhook_listener.route('/message', methods=['POST'])
@validate_twilio_request
def recv_message():
    """Upon reception of a SMS."""
    logger.info(' "/message" reached, IP: %s', request.remote_addr)
    # FB - Format telegram Message
    telegram_message = 'Text from `{From}` ({Country}, {State}) :```   {Body}```'.format(
        From=request.values.get('From', 'unknown'),
        Country=request.values.get('FromCountry', 'unknown'),
        State=request.values.get('FromState', 'unknown'),
        Body=request.values.get('Body', 'unknown')
    )

    logger.info(telegram_message)
    # FB - Send telegram alerts
    tg_send_owner_message('Twilio ID : `{Id}`\n'.format(
        Id=request.values.get('MessageSid', 'unknown')) + telegram_message)
    tg_send_subscribers_message(telegram_message)

    # FB - return empty response to avoid further Twilio fees
    return '<response></response>'



@webhook_listener.route('/call', methods=['POST'])
@validate_twilio_request
def recv_call():
    """Upon reception of a call."""
    logger.info(' "/call" reached, IP: %s', request.remote_addr)
    # FB - Format telegram Message
    telegram_message = 'Call from `{From}` ({Country}, {State}) :```   {Status}```'.format(
        From=request.values.get('From', 'unknown'),
        Country=request.values.get('FromCountry', 'unknown'),
        State=request.values.get('FromState', 'unknown'),
        Status=request.values.get('CallStatus', 'unknown')
    )

    logger.info(telegram_message)
    # FB - Send telegram alerts
    tg_send_owner_message('Twilio ID : `{Id}`\n'.format(
        Id=request.values.get('CallSid', 'unknown')) + telegram_message)
    tg_send_subscribers_message(telegram_message)

    # FB - reject the call without being billed
    return '<Response><Reject/></Response>'


if __name__ == "__main__":
    logger.info('Starting bot')
    # FB - Start the telegram bot
    telegram_bot = tg_bot_start()
    # FB - Start the website
    serve(webhook_listener, host='0.0.0.0', port=80)
