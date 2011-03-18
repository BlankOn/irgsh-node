from celery.worker.control import Panel

from . import manager

@Panel.register
def report_alive(panel):
    manager.ping()

    return {'status': 'ok'}

