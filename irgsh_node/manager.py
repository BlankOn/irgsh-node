import urllib2

from celery.states import STARTED, SUCCESS, RETRY, FAILURE

from .conf import settings
from .utils import send_message

def update_status(task_id, state, message=''):
    host = settings.SERVER.rstrip('/')
    url = '%s/build/%s/status/' % (host, task_id)

    param = {'state': state,
             'message': message}
    send_message(url, param)

def send_log(task_id, fname):
    host = settings.SERVER.rstrip('/')
    url = '%s/build/%s/log/' % (host, task_id)

    param = {'log': open(fname, 'rb')}
    send_message(url, param)

def send_control(task_id, fname):
    host = settings.SERVER.rstrip('/')
    url = '%s/build/%s/info/' % (host, task_id)

    param = {'control': open(fname, 'rb')}
    send_message(url, param)

