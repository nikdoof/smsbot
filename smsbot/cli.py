import argparse
import asyncio
import logging
import os
import sys
from configparser import ConfigParser
from signal import SIGINT, SIGTERM
from twilio.rest import Client

import uvicorn
from asgiref.wsgi import WsgiToAsgi

from smsbot.telegram import TelegramSmsBot
from smsbot.utils import get_smsbot_version
from smsbot.webhook import TwilioWebhookHandler


def main():
    parser = argparse.ArgumentParser("smsbot")
    parser.add_argument(
        "-c",
        "--config",
        default=os.environ.get("SMSBOT_CONFIG_FILE", "config.ini"),
        type=argparse.FileType("r"),
        help="Path to the config file",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--log-file", type=argparse.FileType("a"), help="Path to the log file", default=sys.stdout)
    args = parser.parse_args()

    if args.debug:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level, stream=args.log_file)
    logging.info("smsbot v%s", get_smsbot_version())
    logging.debug("Arguments: %s", args)

    # Load configuration ini file if provided
    config = ConfigParser()
    if args.config:
        logging.info("Loading configuration from %s", args.config.name)
        config.read_file(args.config)

    # Override with environment variables, named SMSBOT_<SECTION>_<VALUE>
    for key, value in os.environ.items():
        if key.startswith("SMSBOT_"):
            logging.debug("Overriding config %s with value %s", key, value)
            section, option = key[7:].split("_", 1)
            config[section][option] = value

    # Validate configuration
    if not config.has_section("telegram") or not config.get("telegram", "bot_token"):
        logging.error(
            "Telegram bot token is required, define a token either in the config file or as an environment variable."
        )
        return

    if config.has_section("twilio") and not (config.get("twilio", "account_sid") and config.get("twilio", "auth_token") and config.get("twilio", "from_number")):
        logging.error(
            "Twilio account SID, auth token, and from number are required for outbound SMS functionality, define them in the config file or as environment variables."
        )
        return

    # Now the config is loaded, set the logger level
    level = getattr(logging, config.get("logging", "level", fallback="INFO").upper(), logging.INFO)
    logging.getLogger().setLevel(level)

    # Configure Twilio client if we have credentials
    if config.has_section("twilio") and config.get("twilio", "account_sid") and config.get("twilio", "auth_token"):
        twilio_client = Client(
            config.get("twilio", "account_sid"),
            config.get("twilio", "auth_token"),
        )
    else:
        twilio_client = None
        logging.warning("No Twilio credentials found, outbound SMS functionality will be disabled.")

    # Start bot
    telegram_bot = TelegramSmsBot(
        token=config.get("telegram", "bot_token"),
        twilio_client=twilio_client,
        twilio_from_number=config.get("twilio", "from_number", fallback=None),
    )

    # Set the owner ID if configured
    if config.has_option("telegram", "owner_id"):
        telegram_bot.owners = [config.getint("telegram", "owner_id")]
    else:
        logging.warning("No Owner ID is set, which is not a good idea...")

    # Add default subscribers
    if config.has_option("telegram", "subscribers"):
        for chat_id in config.get("telegram", "subscribers").split(","):
            telegram_bot.subscribers.append(int(chat_id.strip()))

    # Init the webhook handler
    webhooks = TwilioWebhookHandler(
        account_sid=config.get("twilio", "account_sid", fallback=None),
        auth_token=config.get("twilio", "auth_token", fallback=None),
    )
    webhooks.set_telegram_application(telegram_bot)

    # Build a uvicorn ASGI server
    flask_app = uvicorn.Server(
        config=uvicorn.Config(
            app=WsgiToAsgi(webhooks.app),
            port=config.getint("webhook", "port", fallback=5000),
            use_colors=False,
            host=config.get("webhook", "host", fallback="127.0.0.1"),
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
