import logging

from prometheus_client import Counter, Summary
from telegram.ext import CommandHandler, Updater

from smsbot.utils import get_smsbot_version

REQUEST_TIME = Summary(
    "telegram_request_processing_seconds", "Time spent processing request"
)
COMMAND_COUNT = Counter("telegram_command_count", "Total number of commands processed")


class TelegramSmsBot(object):
    def __init__(
        self, telegram_token, allow_subscribing=False, owner=None, subscribers=None
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.bot_token = telegram_token
        self.subscriber_ids = subscribers or []
        self.set_owner(owner)

        self.updater = Updater(self.bot_token, use_context=True)
        self.updater.dispatcher.add_handler(CommandHandler("help", self.help_handler))
        self.updater.dispatcher.add_handler(CommandHandler("start", self.help_handler))

        if allow_subscribing:
            self.updater.dispatcher.add_handler(
                CommandHandler("subscribe", self.subscribe_handler)
            )
            self.updater.dispatcher.add_handler(
                CommandHandler("unsubscribe", self.unsubscribe_handler)
            )

        self.updater.dispatcher.add_error_handler(self.error_handler)

    def start(self):
        self.logger.info("Starting bot...")
        self.updater.start_polling()
        self.bot = self.updater.bot
        self.logger.info("Bot Ready")

    def stop(self):
        self.updater.stop()

    @REQUEST_TIME.time()
    def help_handler(self, update, context):
        """Send a message when the command /help is issued."""
        self.logger.info("/help command received in chat: %s", update.message.chat)

        commands = []
        for command in self.updater.dispatcher.handlers[0]:
            commands.extend(["/{0}".format(cmd) for cmd in command.command])

        update.message.reply_markdown(
            "Smsbot v{0}\n\n{1}".format(get_smsbot_version(), "\n".join(commands))
        )
        COMMAND_COUNT.inc()

    @REQUEST_TIME.time()
    def subscribe_handler(self, update, context):
        self.logger.info("/subscribe command received")
        if update.message.chat["id"] not in self.subscriber_ids:
            self.logger.info("{0} subscribed".format(update.message.chat["username"]))
            self.subscriber_ids.append(update.message.chat["id"])
            self.send_owner(
                "{0} has subscribed".format(update.message.chat["username"])
            )
            update.message.reply_markdown(
                "You have been subscribed to SMS notifications"
            )
        else:
            update.message.reply_markdown(
                "You are already subscribed to SMS notifications"
            )
        COMMAND_COUNT.inc()

    @REQUEST_TIME.time()
    def unsubscribe_handler(self, update, context):
        self.logger.info("/unsubscribe command received")
        if update.message.chat["id"] in self.subscriber_ids:
            self.logger.info("{0} unsubscribed".format(update.message.chat["username"]))
            self.subscriber_ids.remove(update.message.chat["id"])
            self.send_owner(
                "{0} has unsubscribed".format(update.message.chat["username"])
            )
            update.message.reply_markdown(
                "You have been unsubscribed to SMS notifications"
            )
        else:
            update.message.reply_markdown("You are not subscribed to SMS notifications")
        COMMAND_COUNT.inc()

    def error_handler(self, update, context):
        """Log Errors caused by Updates."""
        self.logger.warning('Update "%s" caused error "%s"', update, context.error)
        self.send_owner(
            'Update "%{0}" caused error "{1}"'.format(update, context.error)
        )

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
        if self.owner_id and self.owner_id not in self.subscriber_ids:
            self.subscriber_ids.append(self.owner_id)

    def add_subscriber(self, chat_id):
        self.subscriber_ids.append(chat_id)
