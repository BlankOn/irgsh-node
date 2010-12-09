import urllib2

from celery.states import STARTED, SUCCESS, RETRY, FAILURE

from .conf import settings
from .utils import send_message

def update_status(task_id, state, message=''):
    host = settings.MANAGER_URL.rstrip('/')
    url = '%s/status/%s/' % (host, task_id)

    param = {'state': state,
             'message': message}
    send_message(url, param)
