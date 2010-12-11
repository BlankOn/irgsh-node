import urllib

from .conf import settings

def send_message(url, param=None):
    opts = {}
    if settings.SSL_CERT is not None:
        opts['cert_file'] = settings.SSL_CERT
    if settings.SSL_KEY is not None:
        opts['key_file'] = settings.SSL_KEY

    data = None
    has_file = False
    headers = {}
    if param is not None:
        has_file = any([type(value) == file for value in param.values()])
        if has_file:
            data, headers = multipart_encode(param)
        else:
            data = urllib.urlencode(param)

    opener = urllib.URLopener(**opts)
    for key, value in headers.items():
        opener.addheader(key, value)
    opener.open(url, data)

