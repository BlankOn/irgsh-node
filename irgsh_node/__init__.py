__version__ = '0.5'

import logging

def setup_logging():
    log = logging.getLogger('irgsh_node')
    log.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)

setup_logging()

def patch_amqplib():
    import sys
    import os
    if not os.environ.has_key('IRGSH_PATCHED_AMQPLIB'):
        from irgsh_node import amqplibssl
        sys.modules['amqplib'] = amqplibssl
        os.environ['IRGSH_PATCHED_AMQPLIB'] = '1'

patch_amqplib()

