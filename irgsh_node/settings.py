#
# irgsh settings
#

BROKER_HOST = "192.168.56.180"
BROKER_PORT = 5672
BROKER_USER = "irgsh"
BROKER_PASSWORD = "irgsh"
BROKER_VHOST = "irgsh"

CELERY_RESULT_BACKEND = "database"
CELERY_RESULT_DBURI = "sqlite:///celerydb.sqlite"
CELERYD_CONCURRENCY = 1

ARCHITECTURE = 'i386'


### STOP #############################################################
# Do not change anything beyond this point.

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

