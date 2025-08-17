from importlib.metadata import version


def get_smsbot_version() -> str:
    return version("smsbot")
