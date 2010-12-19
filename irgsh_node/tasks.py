import os
import gzip
from datetime import timedelta

from celery.task import Task, PeriodicTask

from irgsh.error import IrgshException
from irgsh.packager import Packager
from irgsh.builders.pbuilder import Pbuilder

from irgsh_node.conf import settings
from irgsh_node.localqueue import Queue
from irgsh_node import manager, consts

class BuildPackage(Task):
    exchange = 'builder'
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
                      resultdir, stdout, stderr, kwargs)

        finally:
            if logger is not None:
                logger.close()

    def _run(self, task_id, distribution, specification,
             resultdir, stdout, stderr, kwargs):
        clog = self.get_logger(**kwargs)
        self.update_status(task_id, manager.STARTED)

        # Create and prepare builder (pbuilder)
        pbuilder_path = settings.PBUILDER_PATH
        builder = Pbuilder(distribution, pbuilder_path)

        # Build package
        clog.info('Building package %s for %s' % (specification.location,
                                                  distribution.name))
        packager = Packager(specification, builder, resultdir,
                            stdout=stdout, stderr=stderr)
        packager.build()

    def on_success(self, retval, task_id, args, kwargs):
        distribution, specification = args

        self.update_status(task_id, manager.SUCCESS)
        self.upload_package(task_id, args[0], retval)
        self.upload_log(task_id, kwargs['task_retries'])

        clog = self.get_logger(**kwargs)
        clog.info('Package %s for %s built successfully' % \
                  (specification.location, distribution.name))

    def on_retry(self, exc, task_id, args, kwargs, einfo=None):
        distribution, specification = args

        self.update_status(task_id, manager.RETRY)
        self.upload_log(task_id, kwargs['task_retries'])

        clog = self.get_logger(**kwargs)
        clog.info('Package %s for %s failed to build, retrying..' % \
                  (specification.location, distribution.name))

    def on_failure(self, exc, task_id, args, kwargs, einfo=None):
        distribution, specification = args

        self.update_status(task_id, manager.FAILURE)
        self.upload_log(task_id, kwargs['task_retries'])

        clog = self.get_logger(**kwargs)
        clog.info('Package %s for %s failed to build' % \
                  (specification.location, distribution.name))

    def upload_package(self, task_id, distribution, changes):
        extra = {'distribution': {'name': distribution.name,
                                  'mirror': distribution.mirror,
                                  'dist': distribution.dist,
                                  'components': distribution.components,
                                  'extra': distribution.extra}}

        self.upload(task_id, 'result/%s' % changes, consts.TYPE_RESULT, extra)

    def update_status(self, task_id, status, message=''):
        try:
            manager.update_status(task_id, status, message)
        except IOError:
            pass

    def upload_log(self, task_id, index):
        self.upload(task_id, 'logs/log.%s.gz' % index, consts.TYPE_LOG)

    def upload(self, task_id, path, content_type, extra={}):
        data = {}
        data.update(extra)
        data.update({'task_id': task_id,
                     'path': path,
                     'content_type': content_type})

        queue = Queue(settings.LOCAL_DATABASE)
        queue.put(data)

