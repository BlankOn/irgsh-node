import os
import logging
import time
import tempfile
from cStringIO import StringIO
from urllib2 import HTTPError

from irgsh.distribution import Distribution
from irgsh.uploaders import UploadFailedError
from irgsh.uploaders.dput import Dput

from irgsh_node.conf import settings
from irgsh_node.localqueue import Queue
from irgsh_node import manager, consts

class Uploader(object):
    def __init__(self):
        super(Uploader, self).__init__()

        self.stopped = True
        self.log = logging.getLogger('irgsh_node.uploader')
        self.queue = Queue(settings.LOCAL_DATABASE)

    def stop(self):
        self.stopped = True

    def start(self):
        self.run()

    def run(self):
        delay = 0.1

        self.log.info('Uploader started')
        self.stopped = False
        while not self.stopped:
            time.sleep(delay)

            # Get last item in the upload queue
            item = self.queue.get()
            if item is None:
                delay = delay * 2
                if delay > 5:
                    delay = 5
                continue
            delay = 0.1

            self.log.debug('Got a new item to upload, id=%s' % item.id)

            data = item.payload
            content_type = data['content_type']
            task_id = data['task_id']
            path = data['path']

            # Check if the file exists
            taskdir = os.path.join(settings.RESULT_DIR, task_id)
            fname = os.path.join(taskdir, path)
            if not os.path.exists(fname):
                self.log.error('File not found: %s' % fname)
                continue

            # Upload it
            reset = False
            try:
                if content_type == consts.TYPE_RESULT:
                    distribution = Distribution(**data['distribution'])
                    self.send_result(task_id, distribution, fname)
                elif content_type == consts.TYPE_LOG:
                    manager.send_log(task_id, fname)
                else:
                    self.queue.remove(item)
                    self.log.error('Unrecognized content type: %s' % content_type)
                    continue

                # Success! Remove item from the queue
                self.queue.remove(item)
                self.log.debug('Data uploaded')

            except UploadFailedError, e:
                self.log.error(str(e))
                # TODO: add task log remotely
                # manager.send_log(task_id, 'Failed to upload result: (%s) %s' % \
                #                  (e.code, e.log))
                manager.update_status(task_id, manager.FAILED)

            except IOError, e:
                reset = True
                if isinstance(e, HTTPError):
                    if e.code == 404:
                        self.log.error('Task is not registered')
                        reset = False

            if reset:
                # Fail! Reset item so it will be picked up again
                self.queue.reset(item)
                self.log.error('Failed to upload, send item back to queue: %s' % e)

    def send_result(self, task_id, distribution, changes):
        manager.update_status(task_id, manager.UPLOADING)

        try:
            fd, log = tempfile.mkstemp('-irgsh-upload')
            flog = open(log, 'wb')
            stdout = stderr = flog
            
            opts = {'user': settings.UPLOAD_USER,
                    'host': settings.UPLOAD_HOST,
                    'path': settings.UPLOAD_PATH}
            dput = Dput(distribution, **opts)
            dput.upload(changes, stdout, stderr)

            flog.close()

        except UploadFailedError, e:
            flog.close()

            e.log = open(log).read()
            raise e

        finally:
            os.unlink(log)

        manager.update_status(task_id, manager.FINISHED)

def main():
    uploader = Uploader()
    uploader.start()

    # TODO
    # - add ability to launch multiple uploaders
    # - catch SIGTERM/Ctrl+C and perform warm shutdown
    #   (tell all workers to finish ongoing upload but do not proceed
    #    to the next item in the queue)
    # - if SIGTERM is received again, force all workers to stop


if __name__ == '__main__':
    main()

