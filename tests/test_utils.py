from smsbot.utils.twilio import TwilioMessage


def test_twiliomessage_normal():
    instance = TwilioMessage(
        {
            "From": "+1234567890",
            "To": "+0987654321",
            "Body": "Hello, world!",
            "NumMedia": "2",
            "MediaUrl0": "http://example.com/media1.jpg",
            "MediaUrl1": "http://example.com/media2.jpg",
        }
    )

    assert instance.from_number == "+1234567890"
    assert instance.to_number == "+0987654321"
    assert instance.body == "Hello, world!"
    assert instance.media == [
        "http://example.com/media1.jpg",
        "http://example.com/media2.jpg",
    ]


def test_twiliomessage_no_media():
    instance = TwilioMessage(
        {
            "From": "+1234567890",
            "To": "+0987654321",
            "Body": "Hello, world!",
        }
    )

    assert instance.media == []


def test_twiliomessage_invalid_media_count():
    instance = TwilioMessage(
        {
            "From": "+1234567890",
            "To": "+0987654321",
            "Body": "Hello, world!",
            "NumMedia": "0",
            "MediaUrl0": "http://example.com/media1.jpg",
            "MediaUrl1": "http://example.com/media2.jpg",
        }
    )

    assert instance.media == []

def test_twiliomessage_invalid_media_count_extra():
    instance = TwilioMessage(
        {
            "From": "+1234567890",
            "To": "+0987654321",
            "Body": "Hello, world!",
            "NumMedia": "5",
            "MediaUrl0": "http://example.com/media1.jpg",
            "MediaUrl1": "http://example.com/media2.jpg",
        }
    )

    assert instance.media == [
        "http://example.com/media1.jpg",
        "http://example.com/media2.jpg",
        None,
        None,
        None,
    ]
