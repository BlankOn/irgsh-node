import logging
import time

from irgsh_node.models import get_session, UploadQueue, CT_RESULT, CT_LOG

class Uploader(object):
    def __init__(self, delay=60):
        super(Uploader, self).__init__()

        self.delay = delay
        self.stopped = True
        self.log = logging.getLogger('irgsh_node.uploader')

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
            # 4. mark item as uploaded and notify manager upon successful upload
            # 5. otherwise, update timestamp so it will have lower priority
            #    in the next run

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

