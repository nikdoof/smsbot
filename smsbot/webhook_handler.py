
import os
from functools import wraps

from flask import Flask, abort, current_app, request
from twilio.request_validator import RequestValidator
from waitress import serve

from smsbot.utils import get_smsbot_version


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

    def set_bot(self, bot):  # noqa: WPS615
        self.bot = bot

    def index(self):
        return ''

    def health(self):
        return '<h1>Smsbot v{0}</h1><p><b>Owner</b>: {1}</p><p><b>Subscribers</b>: {2}</p>'.format(get_smsbot_version(), self.bot.owner_id, self.bot.subscriber_ids)

    @validate_twilio_request
    def message(self):
        current_app.logger.info('Received SMS from {From}: {Body}'.format(**request.values.to_dict()))

        message = 'From: {From}\n\n{Body}'.format(**request.values.to_dict())
        self.bot.send_subscribers(message)

        # Return a blank response
        return '<response></response>'

    @validate_twilio_request
    def call(self):
        current_app.logger.info('Received Call from {From}'.format(**request.values.to_dict()))
        self.bot.send_subscribers('Received Call from {From}, rejecting.'.format(**request.values.to_dict()))
        
        # Always reject calls
        return '<Response><Reject/></Response>'

    def serve(self, host='0.0.0.0', port=80, debug=False):
        serve(self.app, host=host, port=port)
