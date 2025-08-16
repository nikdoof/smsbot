import logging

from prometheus_client import Counter, Summary
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    CommandHandler,
    ContextTypes,
    TypeHandler,
)

from smsbot.utils import get_smsbot_version

REQUEST_TIME = Summary(
    "telegram_request_processing_seconds", "Time spent processing request"
)
COMMAND_COUNT = Counter("telegram_command_count", "Total number of commands processed")


class TelegramSmsBot:
    def __init__(self, token: str, owners: list[int] = [], subscribers: list[int] = []):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.app = Application.builder().token(token).build()
        self.owners = owners
        self.subscribers = subscribers

        self.init_handlers()

    def init_handlers(self):
        self.app.add_handler(TypeHandler(Update, self.callback), -1)
        self.app.add_handler(CommandHandler(["help", "start"], self.handler_help))
        self.app.add_handler(CommandHandler("subscribe", self.handler_subscribe))
        self.app.add_handler(CommandHandler("unsubscribe", self.handler_unsubscribe))

    async def callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the update"""
        if update.effective_user.id in self.owners:
            self.logger.info(
                f"{update.effective_user.username} sent {update.message.text}"
            )
            COMMAND_COUNT.inc()
        else:
            self.logger.debug(f"Ignoring message from user {update.effective_user.id}")
            raise ApplicationHandlerStop

    async def send_message(self, chat_id: int, text: str):
        """Send a message to a specific chat"""
        self.logger.info(f"Sending message to chat {chat_id}: {text}")
        await self.app.bot.send_message(
            chat_id=chat_id, text=text, parse_mode="MarkdownV2"
        )

    async def send_subscribers(self, text: str):
        """Send a message to all subscribers"""
        for subscriber in self.subscribers:
            self.logger.info(f"Sending message to subscriber {subscriber}")
            await self.send_message(subscriber, text)

    async def send_owners(self, text: str):
        """Send a message to all owners"""
        for owner in self.owners:
            self.logger.info(f"Sending message to owner {owner}")
            await self.send_message(owner, text)

    @REQUEST_TIME.time()
    async def handler_help(self, update, context):
        """Send a message when the command /help is issued."""
        self.logger.info("/help command received in chat: %s", update.message.chat)

        commands = []
        for command in self.app.handlers[0]:
            if isinstance(command, CommandHandler):
                commands.extend(["/{0}".format(cmd) for cmd in command.commands])

        await update.message.reply_markdown(
            "Smsbot v{0}\n\n{1}".format(get_smsbot_version(), "\n".join(commands))
        )
        COMMAND_COUNT.inc()

    @REQUEST_TIME.time()
    async def handler_subscribe(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle subscription requests"""
        user_id = update.effective_user.id
        if user_id not in self.subscribers:
            self.subscribers.append(user_id)
            self.logger.info(f"User {user_id} subscribed.")
            self.logger.info(f"Current subscribers: {self.subscribers}")
            await update.message.reply_markdown(
                "You have successfully subscribed to updates."
            )
        else:
            self.logger.info(f"User {user_id} is already subscribed.")

    @REQUEST_TIME.time()
    async def handler_unsubscribe(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle unsubscription requests"""
        user_id = update.effective_user.id
        if user_id in self.subscribers:
            self.subscribers.remove(user_id)
            self.logger.info(f"User {user_id} unsubscribed.")
            self.logger.info(f"Current subscribers: {self.subscribers}")
            await update.message.reply_markdown(
                "You have successfully unsubscribed from updates."
            )
        else:
            self.logger.info(f"User {user_id} is not subscribed.")
