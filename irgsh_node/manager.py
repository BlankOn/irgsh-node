import urllib2
import json

from .conf import settings
from .utils import send_message

CANCELLED = -2
FAILED = -1
WAITING = 0
PREPARING = 100
DOWNLOADING_SOURCE = 101
DOWNLOADING_ORIG = 102
BUILDING = 103
BUILT = 104
UPLOADING = 201
FINISHED = 999

URL_UPDATE_STATUS = '%(host)s/task/%(task_id)s/status/'
URL_BUILD_LOG = '%(host)s/task/%(task_id)s/log/'
URL_CHANGES = '%(host)s/task/%(task_id)s/changes/'
URL_CONTROL = '%(host)s/task/%(task_id)s/info/'
URL_GET_STATUS = '%(host)s/build/%(spec_id)s/status/'
URL_PING = '%(host)s/builder/%(name)s/ping/'

def update_status(task_id, status):
    host = settings.SERVER.rstrip('/')
    url = URL_UPDATE_STATUS % {'host': host, 'task_id': task_id}

    param = {'status': status,
             'builder': settings.NODE_NAME}
    send_message(url, param)

def send_log(task_id, fname):
    host = settings.SERVER.rstrip('/')
    url = URL_BUILD_LOG % {'host': host, 'task_id': task_id}

    param = {'log': open(fname, 'rb'),
             'builder': settings.NODE_NAME}
    send_message(url, param)

def send_changes(task_id, fname):
    host = settings.SERVER.rstrip('/')
    url = URL_CHANGES % {'host': host, 'task_id': task_id}

    param = {'changes': open(fname, 'rb'),
             'builder': settings.NODE_NAME}
    send_message(url, param)

def send_control(task_id, fname):
    host = settings.SERVER.rstrip('/')
    url = URL_CONTROL % {'host': host, 'task_id': task_id}

    param = {'control': open(fname, 'rb'),
             'builder': settings.NODE_NAME}
    send_message(url, param)

def get_spec_status(spec_id):
    host = settings.SERVER.rstrip('/')
    url = URL_GET_STATUS % {'host': host, 'spec_id': spec_id}

    return json.loads(send_message(url))

def ping():
    host = settings.SERVER.rstrip('/')
    name = settings.NODE_NAME
    url = URL_PING % {'host': host, 'name': name}

    status = 'idle' # None # TODO: idle, building #task_id
    param = {'status': status,
             'builder': settings.NODE_NAME}
    send_message(url, param)

