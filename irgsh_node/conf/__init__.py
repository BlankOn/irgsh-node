"""
Settings and configuration for irgsh-node.

This module is heavily influenced by and has some codes borrowed from Django.
Licensed under BSD License.
"""

import os
from ConfigParser import SafeConfigParser, NoOptionError

from importlib import import_module

from irgsh_node.conf import global_settings

ENVIRONMENT_VARIABLE = 'IRGSH_NODE_CONFIG'

CONFIG_MAPPING = {
    'irgsh': {
        'node-name': 'NODE_NAME',
        'build-path': 'BUILD_PATH',
        'server': 'SERVER',
        'cert': 'SSL_CERT',
        'cert-key': 'SSL_KEY',
        'arch': 'ARCHITECTURE',
    }
}
CONFIG_REQUIRED = CONFIG_MAPPING.keys() # all are required

def init_settings(settings):
    # Define celery queues
    arch = settings.ARCHITECTURE
    settings.CELERY_QUEUES = {
        'builder': {
            'exchange': 'builder',
            'exchange_type': 'topic',
            'binding_key': 'builder.%s' % arch
        }
    }
    settings.CELERY_DEFAULT_QUEUE = 'builder'
    settings.CELERY_DEFAULT_EXCHANGE = 'builder'
    settings.CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
    settings.CELERY_DEFAULT_ROUTING_KEY = 'builder.%s' % arch

    imports = getattr(settings, 'CELERY_IMPORTS', ())
    settings.CELERY_IMPORTS = ('irgsh_node.tasks',) + imports

def load_config(config_file):
    # Check file existance
    if not os.path.exists(config_file):
        raise IOError, 'File not found'

    # Load config
    cp = SafeConfigParser()
    cp.read(config_file)

    # Load config values
    config = {}
    for section in CONFIG_MAPPING:
        for key, name in CONFIG_MAPPING[section].items():
            try:
                value = cp.get(section, key)
                config[name] = value
            except NoOptionError:
                if key in CONFIG_REQUIRED:
                    raise ValueError, 'Key not found: %s' % key

    return config

class Settings(object):
    def __init__(self, config_file):
        # Load default settings
        for setting in dir(global_settings):
            if setting == setting.upper():
                setattr(self, setting, getattr(global_settings, setting))

        # Load configuration_file
        if not os.path.exists(config_file):
            raise IOError("Could not load configuration file '%s'" % \
                          config_file)

        try:
            config = load_config(config_file)
        except ValueError, e:
            raise ValueError, "Unable to read configuration file '%s': %s" % \
                              (config_file, e)
        except IOError, e:
            raise IOError, "Unable to read configuration file '%s': %s" % \
                           (config_file, e)

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
        try:
            config_file = os.environ[ENVIRONMENT_VARIABLE]
            if not config_file:
                raise KeyError
        except KeyError:
            raise ImportError('Settings cannot be imported, because ' \
                              'environment variable %s is undefined' % 
                              ENVIRONMENT_VARIABLE)

        self._settings = Settings(config_file)
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

