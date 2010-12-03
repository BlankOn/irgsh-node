import celery
import os

def main():
    os.environ['CELERY_CONFIG_MODULE'] = 'irgsh_node.celeryconfig'
    from celery.bin import celeryd
    celeryd.main()

if __name__ == '__main__':
    main()

