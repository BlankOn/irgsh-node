import urllib

from .conf import settings

def send_message(url, param=None):
    opts = {}
    if settings.SSL_CERT is not None:
        opts['cert_file'] = settings.SSL_CERT
    if settings.SSL_KEY is not None:
        opts['key_file'] = settings.SSL_KEY

    data = None
    if param is not None:
        data = urllib.urlencode(param)
    opener = urllib.URLopener(**opts)
    opener.open(url, data)

def send_file(url, param=None):
    pass

