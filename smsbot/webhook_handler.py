
import os
from functools import wraps

from flask import Flask, abort, current_app, request
from twilio.request_validator import RequestValidator
from waitress import serve

from smsbot.utils import get_smsbot_version

from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import make_wsgi_app, Counter, Summary

REQUEST_TIME = Summary('webhook_request_processing_seconds', 'Time spent processing request')
MESSAGE_COUNT = Counter('webhook_message_count', 'Total number of messages processed')
CALL_COUNT = Counter('webhook_call_count', 'Total number of calls processed')


def validate_twilio_request(func):
    """Validates that incoming requests genuinely originated from Twilio"""
    @wraps(func)
    def decorated_function(*args, **kwargs):  # noqa: WPS430
        # Create an instance of the RequestValidator class
        twilio_token = os.environ.get('SMSBOT_TWILIO_AUTH_TOKEN')

        if not twilio_token:
            current_app.logger.warning('Twilio request validation skipped due to SMSBOT_TWILIO_AUTH_TOKEN missing')
            return func(*args, **kwargs)

        validator = RequestValidator(twilio_token)

        # Validate the request using its URL, POST data,
        # and X-TWILIO-SIGNATURE header
        request_valid = validator.validate(
            request.url,
            request.form,
            request.headers.get('X-TWILIO-SIGNATURE', ''),
        )

        # Continue processing the request if it's valid, return a 403 error if
        # it's not
        if request_valid or current_app.debug:
            return func(*args, **kwargs)
        return abort(403)
    return decorated_function


class TwilioWebhookHandler(object):

    def __init__(self):
        self.app = Flask(self.__class__.__name__)
        self.app.add_url_rule('/', 'index', self.index, methods=['GET'])
        self.app.add_url_rule('/health', 'health', self.health, methods=['GET'])
        self.app.add_url_rule('/message', 'message', self.message, methods=['POST'])
        self.app.add_url_rule('/call', 'call', self.call, methods=['POST'])

        # Add prometheus wsgi middleware to route /metrics requests
        self.app.wsgi_app = DispatcherMiddleware(self.app.wsgi_app, {
            '/metrics': make_wsgi_app(),
        })

    def set_bot(self, bot):  # noqa: WPS615
        self.bot = bot

    def index(self):
        return ''

    @REQUEST_TIME.time()
    def health(self):
        return {
            'version': get_smsbot_version(),
            'owner': self.bot.owner_id,
            'subscribers': self.bot.subscriber_ids,
        }

    @REQUEST_TIME.time()
    @validate_twilio_request
    def message(self):
        current_app.logger.info('Received SMS from {From}: {Body}'.format(**request.values.to_dict()))

        message = 'From: {From}\n\n{Body}'.format(**request.values.to_dict())
        self.bot.send_subscribers(message)

        # Return a blank response
        MESSAGE_COUNT.inc()
        return '<response></response>'

    @REQUEST_TIME.time()
    @validate_twilio_request
    def call(self):
        current_app.logger.info('Received Call from {From}'.format(**request.values.to_dict()))
        self.bot.send_subscribers('Received Call from {From}, rejecting.'.format(**request.values.to_dict()))

        # Always reject calls
        CALL_COUNT.inc()
        return '<Response><Reject/></Response>'

    def serve(self, host='0.0.0.0', port=80, debug=False):
        serve(self.app, host=host, port=port)
