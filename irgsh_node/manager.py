import urllib2

from .conf import settings
from .utils import send_message

FAILED = -1
WAITING = 0
PREPARING = 100
DOWNLOADING_SOURCE = 101
DOWNLOADING_ORIG = 102
BUILDING = 102
BUILT = 104
UPLOADING = 201
UPLOADED = 202
FINISHED = 999

HOST = settings.SERVER.rstrip('/')

URL_UPDATE_STATUS = '%s/build/%%(task_id)s/status/' % HOST
URL_BUILD_LOG = '%s/build/%%(task_id)s/log/' % HOST
URL_CONTROL = '%s/build/%%(task_id)s/info/' % HOST

def update_status(task_id, status):
    url = URL_UPDATE_STATUS % {'task_id': task_id}

    param = {'status': status,
             'builder': settings.NODE_NAME}
    send_message(url, param)

def send_log(task_id, fname):
    url = URL_BUILD_LOG % {'task_id': task_id}

    param = {'log': open(fname, 'rb'),
             'builder': settings.NODE_NAME}
    send_message(url, param)

def send_control(task_id, fname):
    url = URL_CONTROL % {'task_id': task_id}

    param = {'control': open(fname, 'rb'),
             'builder': settings.NODE_NAME}
    send_message(url, param)

