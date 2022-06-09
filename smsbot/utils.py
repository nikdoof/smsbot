import pkg_resources


def get_smsbot_version():
    return pkg_resources.require('smsbot')[0].version
