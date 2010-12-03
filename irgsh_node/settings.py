#
# irgsh settings
#

BROKER_HOST = "192.168.56.180"
BROKER_PORT = 5672
BROKER_USER = "irgsh"
BROKER_PASSWORD = "irgsh"
BROKER_VHOST = "irgsh"
BROKER_SSL_KEY = 'etc/ssl.key'
BROKER_SSL_CERT = 'etc/ssl.cert'

CELERY_RESULT_BACKEND = "database"
CELERY_RESULT_DBURI = "sqlite:///celerydb.sqlite"
CELERYD_CONCURRENCY = 1

ARCHITECTURE = 'i386'


### STOP #############################################################
# Do not change anything beyond this point.

#
# load system wide and local settings
#

import os

if os.path.exists('/etc/irgsh/irgsh_node.py'):
    execfile('/etc/irgsh/irgsh_node.py')

if os.path.exists('settings.py'):
    extra = os.path.abspath('settings.py')
    this = os.path.abspath(__file__)
    if this.endswith('.pyc'): this = this[:-1]
    if extra != this:
        execfile('settings.py')

#
# queue definition
#

CELERY_QUEUES = {
    'builder': {
        'exchange': 'builder',
        'binding_key': 'builder.%s' % ARCHITECTURE
    },
}
CELERY_DEFAULT_QUEUE = 'builder'
CELERY_DEFAULT_EXCHANGE = 'builder'
CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_DEFAULT_ROUTING_KEY = 'builder.%s' % ARCHITECTURE

CELERY_IMPORTS = ('irgsh_node.tasks',)

