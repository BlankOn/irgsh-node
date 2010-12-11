import urllib2

from celery.states import STARTED, SUCCESS, RETRY, FAILURE

from .conf import settings
from .utils import send_message

def update_status(task_id, state, message=''):
    host = settings.SERVER.rstrip('/')
    url = '%s/status/%s/' % (host, task_id)

    param = {'state': state,
             'message': message}
    send_message(url, param)

def send_log(task_id, fname):
    host = settings.SERVER.rstrip('/')
    url = '%s/log/%s/' % (host, task_id)

    param = {'log': open(fname, 'rb')}
    send_message(url, param)

