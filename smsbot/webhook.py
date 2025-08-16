from functools import wraps

from flask import Flask, abort, current_app, request
from prometheus_async.aio import time
from prometheus_client import Counter, Summary, make_wsgi_app
from twilio.request_validator import RequestValidator
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from smsbot.utils import TwilioWebhookPayload, get_smsbot_version

REQUEST_TIME = Summary(
    "webhook_request_processing_seconds", "Time spent processing request"
)
MESSAGE_COUNT = Counter("webhook_message_count", "Total number of messages processed")
CALL_COUNT = Counter("webhook_call_count", "Total number of calls processed")



class TwilioWebhookHandler(object):
    def __init__(self, account_sid: str | None = None, auth_token: str | None = None):
        self.app = Flask(self.__class__.__name__)
        self.app.add_url_rule("/", "index", self.index, methods=["GET"])
        self.app.add_url_rule("/health", "health", self.health, methods=["GET"])
        self.app.add_url_rule("/message", "message", self.message, methods=["POST"])
        self.app.add_url_rule("/call", "call", self.call, methods=["POST"])

        self.account_sid = account_sid
        self.auth_token = auth_token

        # Wrap validation around hook endpoints
        self.message = self.validate_twilio_request(self.message)
        self.call = self.validate_twilio_request(self.call)

        # Add prometheus wsgi middleware to route /metrics requests
        self.app.wsgi_app = DispatcherMiddleware(
            self.app.wsgi_app,
            {
                "/metrics": make_wsgi_app(),
            },
        )

    def validate_twilio_request(self, func):
        """Validates that incoming requests genuinely originated from Twilio"""

        @wraps(func)
        async def decorated_function(*args, **kwargs):
            # Create an instance of the RequestValidator class
            if not self.auth_token:
                current_app.logger.warning(
                    "Twilio request validation skipped due to Twilio Auth Token missing"
                )
                return await func(*args, **kwargs)
            validator = RequestValidator(self.auth_token)

            # Validate the request using its URL, POST data,
            # and X-TWILIO-SIGNATURE header
            request_valid = validator.validate(
                request.url,
                request.form,
                request.headers.get("X-TWILIO-SIGNATURE", ""),
            )

            # Continue processing the request if it's valid, return a 403 error if
            # it's not
            if request_valid or current_app.debug:
                return await func(*args, **kwargs)
            return abort(403)

        return decorated_function

    def set_bot(self, bot):
        self.bot = bot

    async def index(self):
        return f'smsbot v{get_smsbot_version()} - <a href="https://github.com/nikdoof/smsbot">GitHub</a>'

    async def health(self):
        """Return basic health information"""
        return {
            "version": get_smsbot_version(),
            "owners": self.bot.owners,
            "subscribers": self.bot.subscribers,
        }

    @time(REQUEST_TIME)
    async def message(self):
        """Handle incoming SMS messages from Twilio"""
        current_app.logger.info(
            "Received SMS from {From}: {Body}".format(**request.values.to_dict())
        )

        await self.bot.send_subscribers(
            TwilioWebhookPayload.parse(request.values.to_dict()).to_markdownv2()
        )

        # Return a blank response
        MESSAGE_COUNT.inc()
        return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'

    @time(REQUEST_TIME)
    async def call(self):
        """Handle incoming calls from Twilio"""
        current_app.logger.info(
            "Received Call from {From}".format(**request.values.to_dict())
        )
        await self.bot.send_subscribers(
            TwilioWebhookPayload.parse(request.values.to_dict()).to_markdownv2()
        )

        # Always reject calls
        CALL_COUNT.inc()
        return '<?xml version="1.0" encoding="UTF-8"?><Response><Reject/></Response>'
