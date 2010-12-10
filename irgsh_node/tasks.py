import os
import gzip
from datetime import timedelta

from celery.task import Task, PeriodicTask

from irgsh.error import IrgshException
from irgsh.packager import Packager
from irgsh.builders.pbuilder import Pbuilder

from irgsh_node.conf import settings
from irgsh_node.models import get_session, UploadQueue, CT_RESULT, CT_LOG
from irgsh_node import manager

class BuildPackage(Task):
    ignore_result = True

    max_retries = 5
    default_retry_delay = 5 * 60

    def run(self, distribution, specification, **kwargs):
        logger = None
        try:
            task_id = kwargs['task_id']
            retries = kwargs['task_retries']

            # Prepare directories
            taskdir = os.path.join(settings.RESULT_DIR, task_id)
            logdir = os.path.join(taskdir, 'logs')
            resultdir = os.path.join(taskdir, 'result')
            for dirname in [logdir, resultdir]:
                if not os.path.exists(dirname):
                    os.makedirs(dirname)

            # Prepare logger
            logname = os.path.join(logdir, 'log.%d.gz' % retries)
            logger = gzip.GzipFile(logname, 'wb')
            stdout = stderr = logger

            # Execute builder
            self._run(task_id, distribution, specification,
                      resultdir, stdout, stderr)

        finally:
            if logger is not None:
                logger.close()

    def _run(self, task_id, distribution, specification,
             resultdir, stdout, stderr):
        clog = self.get_logger(**kwargs)
        manager.update_status(task_id, manager.STARTED)

        # Create and prepare builder (pbuilder)
        pbuilder_path = settings.PBUILDER_PATH
        builder = Pbuilder(distribution, pbuilder_path)
        builder.init()
        if not os.path.exists(builder.configfile):
            clog.info('Creating pbuilder environment for %s' % \
                      distribution.name)
            builder.create()


        # Build package
        clog.info('Building package %s for %s' % (specification.location,
                                                  distribution.name))
        packager = Packager(specification, builder, resultdir,
                            stdout=stdout, stderr=stderr)
        packager.build()

    def on_success(self, retval, task_id, args, kwargs):
        manager.update_status(task_id, manager.SUCCESS)
        self.upload_package(task_id, retval)
        self.upload_log(task_id, kwargs['task_retries'])

        clog = self.get_logger(**kwargs)
        clog.info('Package %s for %s built successfully' % \
                  (specification.location, distribution.name))

    def on_retry(self, exc, task_id, args, kwargs, einfo=None):
        manager.update_status(task_id, manager.RETRY)
        self.upload_log(task_id, kwargs['task_retries'])

        clog = self.get_logger(**kwargs)
        clog.info('Package %s for %s failed to build, retrying..' % \
                  (specification.location, distribution.name))

    def on_failure(self, task_id, args, kwargs, einfo=None):
        manager.update_status(task_id, manager.FAILURE)
        self.upload_log(task_id, kwargs['task_retries'])

        clog = self.get_logger(**kwargs)
        clog.info('Package %s for %s failed to build' % \
                  (specification.location, distribution.name))

    def upload_package(self, task_id, changes):
        self.upload(task_id, 'result/%s' % changes, CT_RESULT)

    def upload_log(self, task_id, index):
        self.upload(task_id, 'logs/log.%s.gz' % index, CT_LOG)

    def upload(self, task_id, path, content_type):
        queue = UploadQueue()
        queue.task_id = task_id
        queue.path = path
        queue.content_type = content_type

        session = get_session()
        session.add(queue)
        session.commit()


class Uploader(PeriodicTask):
    """
    Uploader periodic task.

    Note that celery beat has to be activated.
    """

    run_every = timedelta(seconds=5*60)

    def run(self, **kwargs):
        pass

        # TODO
        # 1. check if previous uploader task is still running
        #    if so, return immediately
        # 2. check upload queue in the local database
        # 3. upload each item in upload queue, ordered by timestamp
        # 4. mark item as uploaded and notify manager upon successful upload
        # 5. otherwise, update timestamp so it will have lower priority
        #    in the next run

