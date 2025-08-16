from importlib.metadata import version


def get_smsbot_version():
    return version("smsbot")


class TwilioMessage:
    """
    Parses a Twilio webhook message.
    """

    def __init__(self, data: dict) -> None:
        self.from_number: str = data.get("From", "Unknown")
        self.to_number: str = data.get("To", "Unknown")
        self.body: str = data.get("Body", "")

        self.media = []
        for i in range(0, int(data.get("NumMedia", "0"))):
            self.media.append(data.get(f"MediaUrl{i}"))

    def _escape(self, text: str) -> str:
        """Escape text for MarkdownV2"""
        characters = [
            "_",
            "*",
            "[",
            "]",
            "(",
            ")",
            "~",
            "`",
            ">",
            "#",
            "+",
            "-",
            "=",
            "|",
            "{",
            "}",
            ".",
            "!",
        ]
        for char in characters:
            text = text.replace(char, rf"\{char}")
        return text

    def __repr__(self) -> str:
        return f"TwilioWebhookMessage(from={self.from_number}, to={self.to_number})"

    def to_str(self) -> str:
        media_str = "\n".join([f"<{url}>" for url in self.media]) if self.media else ""
        msg = f"**From**: {self.from_number}\n**To**: {self.to_number}\n\n{self.body}\n\n{media_str}"
        return msg

    def to_markdownv2(self):
        media_str = "\n".join([f"{self._escape(url)}" for url in self.media]) if self.media else ""
        msg = f"**From**: {self._escape(self.from_number)}\n**To**: {self._escape(self.to_number)}\n\n{self._escape(self.body)}\n\n{media_str}"
        return msg
