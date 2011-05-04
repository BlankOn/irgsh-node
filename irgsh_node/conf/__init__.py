"""
Settings and configuration for irgsh-node.

This module is heavily influenced by and has some codes borrowed from Django.
Licensed under BSD License.
"""

import os
from glob import glob
from ConfigParser import SafeConfigParser, NoOptionError

from importlib import import_module

from irgsh_node.conf import global_settings

ENVIRONMENT_VARIABLE = 'IRGSH_NODE_CONFIG'

CONFIG_MAPPING = {
    'irgsh': {
        'node-name': 'NODE_NAME',
        'result-dir': 'RESULT_DIR',
        'server': 'SERVER',
        'ssl-cert': 'SSL_CERT',
        'ssl-key': 'SSL_KEY',
        'arch': 'ARCHITECTURE',
        'workers': 'CELERYD_CONCURRENCY',
        'db': 'LOCAL_DATABASE',
        'keyring': 'KEYRING',
    },
    'queue': {
        'host': 'BROKER_HOST',
        'port': 'BROKER_PORT',
        'username': 'BROKER_USER',
        'password': 'BROKER_PASSWORD',
        'vhost': 'BROKER_VHOST'
    },
    'pbuilder': {
        'path': 'PBUILDER_PATH'
    },
    'upload': {
        'host': 'UPLOAD_HOST',
        'user': 'UPLOAD_USER',
    }
}
CONFIG_REQUIRED = {
    'irgsh': ['node-name', 'build-path', 'server', 'arch', 'keyring'],
    'queue': ['host', 'vhost'],
    'pbuilder': ['path'],
    'upload': ['user', 'host', 'path'],
}
CONFIG_TYPE_MAPPER = {
    'BROKER_PORT': int
}

def init_settings(settings):
    # Define celery queues
    arch = settings.ARCHITECTURE
    queue = 'builder_%s' % arch
    settings.CELERY_QUEUES = {
        queue: {
            'exchange': 'builder',
            'exchange_type': 'topic',
            'binding_key': 'builder.%s' % arch
        }
    }
    settings.CELERY_DEFAULT_QUEUE = queue
    settings.CELERY_DEFAULT_EXCHANGE = 'builder'
    settings.CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
    settings.CELERY_DEFAULT_ROUTING_KEY = 'builder.%s' % arch

    imports = getattr(settings, 'CELERY_IMPORTS', ())
    task_modules = ('irgsh_node.tasks', 'irgsh_node.control')
    settings.CELERY_IMPORTS = task_modules + imports

def load_config(config_files):
    # Load config
    cp = SafeConfigParser()
    found = False
    for config_file in config_files:
        try:
            if os.path.exists(config_file):
                cp.read(config_file)
                found = True
        except TypeError:
            pass

    if not found:
        raise ValueError

    # Load config values
    config = {}
    for section in CONFIG_MAPPING:
        for key, name in CONFIG_MAPPING[section].items():
            try:
                value = cp.get(section, key)
                config[name] = value
            except NoOptionError:
                if key in CONFIG_REQUIRED[section]:
                    raise ValueError, 'Key not found: %s' % key

    # Type mapping
    for key, mapper in CONFIG_TYPE_MAPPER.items():
        if key in config:
            config[key] = mapper(config[key])

    return config

class Settings(object):
    def __init__(self, config_files):
        # Load default settings
        for setting in dir(global_settings):
            if setting == setting.upper():
                setattr(self, setting, getattr(global_settings, setting))

        # Load configuration_file
        try:
            config = load_config(config_files)
        except ValueError, e:
            raise ValueError, "Unable to read configuration files"

        for key, value in config.items():
            setattr(self, key, value)

        # Fill up dynamic settings
        init_settings(self)

class LazySettings(object):
    '''Lazy settings loader.

    Load settings when it is first used.
    '''
    def __init__(self):
        self._configured = False
        self._settings = None

    def _configure(self):
        config_files = []

        config_files = ['irgsh-node.conf',
                        '/etc/irgsh/node/irgsh-node.conf']
        config_files.append(sorted(
                        glob('/etc/irgsh/node/irgsh-node.conf.d/*.conf')))

        try:
            config_file = os.environ[ENVIRONMENT_VARIABLE]
            config_files.append(config_file)
        except KeyError:
            pass

        self._settings = Settings(config_files)
        self._configured = True

    def __getattr__(self, name):
        if not self._configured:
            self._configure()
        return getattr(self._settings, name)

    def __hasattr__(self, name):
        if not self._configured:
            self._configure()
        return hasattr(self._settings, name)

    def __dir__(self):
        if not self._configured:
            self._configure()
        return dir(self._settings)

settings = LazySettings()

