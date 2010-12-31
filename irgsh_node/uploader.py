import os
import logging
import time
from cStringIO import StringIO

from irgsh.distribution import Distribution
from irgsh.uploaders.dput import Dput

from irgsh_node.conf import settings
from irgsh_node.localqueue import Queue
from irgsh_node import manager, consts

class Uploader(object):
    def __init__(self, delay=60):
        super(Uploader, self).__init__()

        self.delay = delay
        self.stopped = True
        self.log = logging.getLogger('irgsh_node.uploader')
        self.queue = Queue(settings.LOCAL_DATABASE)

    def stop(self):
        self.stopped = True

    def start(self):
        self.run()

    def run(self):
        self.log.info('Uploader started')
        self.stopped = False
        while not self.stopped:
            self.log.info('Uploading..')
            time.sleep(self.delay)

            # Get last item in the upload queue
            item = self.queue.get()
            if item is None:
                continue

            data = item.payload
            content_type = data['content_type']
            task_id = data['task_id']
            path = data['path']

            # Check if the file exists
            taskdir = os.path.join(settings.RESULT_DIR, task_id)
            fname = os.path.join(taskdir, path)
            if not os.path.exists(fname):
                self.log.warning('File not found: %s' % fname)
                continue

            # Upload it
            try:
                if content_type == consts.TYPE_RESULT:
                    distribution = Distribution(**data['distribution'])
                    self.send_result(task_id, distribution, fname)
                elif content_type == consts.TYPE_LOG:
                    manager.send_log(task_id, fname)
                elif content_type == consts.TYPE_CONTROL:
                    manager.send_control(task_id, fname)

                # Success! Remove item from the queue
                self.queue.remove(item)
            except IOError:
                # Fail! Reset item so it will be picked up again
                self.queue.reset(item)

    def send_result(self, task_id, distribution, changes):
        manager.update_status(task_id, manager.UPLOADING)

        stdout = stderr = StringIO()

        dput = Dput(distribution)
        dput.upload(changes, stdout=stdout, stderr=stderr)

        manager.update_status(task_id, manager.UPLOADED)

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

