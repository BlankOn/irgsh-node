import os

DEFAULT_CONFIG_MODULE = 'irgsh_node.settings'

def main():
    if not 'CELERY_CONFIG_MODULE' in os.environ:
        os.environ['CELERY_CONFIG_MODULE'] = DEFAULT_CONFIG_MODULE

    from celery.bin import celeryd
    celeryd.main()

if __name__ == '__main__':
    main()

