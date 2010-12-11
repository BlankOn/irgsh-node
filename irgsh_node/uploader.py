import os
import logging
import time

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

    def run(self):
        self.log.info('Uploader started')
        self.stopped = False
        while not self.stopped:
            self.log.info('Uploading..')
            time.sleep(self.delay)

            # TODO
            # 1. check if previous uploader task is still running
            #    if so, return immediately
            #    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            #    - no need to do the above again because the upload
            #      will be performed sequentially
            #
            # 2. check upload queue in the local database
            # 3. upload each item in upload queue, ordered by timestamp
            item = self.queue.get()
            if item is None:
                continue

            # 4. mark item as uploaded and notify manager upon successful upload
            data = item.payload
            content_type = data['content_type']
            task_id = data['task_id']
            path = data['path']
            if content_type == consts.TYPE_RESULT:
                self.upload_result(task_id, path)
            else:
                self.upload_log(task_id, path)

            # 5. otherwise, update timestamp so it will have lower priority
            #    in the next run

    def upload_result(self, task_id, path):
        pass

    def upload_log(self, task_id, path):
        taskdir = os.path.join(settings.RESULT_DIR, task_id)
        fname = os.path.join(taskdir, path)
        if not os.path.exists(fname):
            return

        manager.send_log(task_id, fname)

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

