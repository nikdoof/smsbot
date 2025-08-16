import argparse
import asyncio
import logging
import os
from signal import SIGINT, SIGTERM

import uvicorn
from asgiref.wsgi import WsgiToAsgi

from smsbot.telegram import TelegramSmsBot
from smsbot.utils import get_smsbot_version
from smsbot.webhook_handler import TwilioWebhookHandler


def main():
    parser = argparse.ArgumentParser("smsbot")
    parser.add_argument(
        "--listen-host", default=os.environ.get("SMSBOT_LISTEN_HOST") or "0.0.0.0"
    )
    parser.add_argument(
        "--listen-port", default=os.environ.get("SMSBOT_LISTEN_PORT") or 80, type=int
    )
    parser.add_argument(
        "--telegram-bot-token", default=os.environ.get("SMSBOT_TELEGRAM_BOT_TOKEN")
    )
    parser.add_argument("--owner-id", default=os.environ.get("SMSBOT_OWNER_ID"))
    parser.add_argument(
        "--default-subscribers", default=os.environ.get("SMSBOT_DEFAULT_SUBSCRIBERS")
    )
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if args.debug:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level)
    logging.info("smsbot v%s", get_smsbot_version())
    logging.debug("Arguments: %s", args)

    # Start bot
    telegram_bot = TelegramSmsBot(token=args.telegram_bot_token)

    # Set the owner ID if configured
    if args.owner_id:
        telegram_bot.owners = [int(args.owner_id)]
    else:
        logging.warning("No Owner ID is set, which is not a good idea...")

    # Add default subscribers
    if args.default_subscribers:
        for chat_id in args.default_subscribers.split(","):
            telegram_bot.subscribers.append(int(chat_id.strip()))

    webhooks = TwilioWebhookHandler()
    webhooks.set_bot(telegram_bot)

    # Build a uvicorn ASGI server
    flask_app = uvicorn.Server(
        config=uvicorn.Config(
            app=WsgiToAsgi(webhooks.app),
            port=args.listen_port,
            use_colors=False,
            host=args.listen_host,
        )
    )

    # Loop until exit
    loop = asyncio.get_event_loop()
    main_task = asyncio.ensure_future(run_bot(telegram_bot, flask_app))
    for signal in [SIGINT, SIGTERM]:
        loop.add_signal_handler(signal, main_task.cancel)
    try:
        loop.run_until_complete(main_task)
    # Catch graceful shutdowns
    except asyncio.CancelledError:
        pass
    finally:
        loop.close()


async def run_bot(telegram_bot: TelegramSmsBot, flask_app):
    # Start async Telegram bot
    try:
        # Start the bot
        await telegram_bot.app.initialize()
        await telegram_bot.app.start()
        await telegram_bot.app.updater.start_polling()

        # Startup uvicorn/flask
        await flask_app.serve()

        # Run the bot idle loop
        await telegram_bot.app.updater.idle()
    finally:
        # Shutdown in reverse order
        await flask_app.shutdown()
        await telegram_bot.app.updater.stop()
        await telegram_bot.app.stop()
        await telegram_bot.app.shutdown()
