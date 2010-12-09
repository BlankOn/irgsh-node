import os
import gzip

from celery.task import Task

from irgsh.error import IrgshException
from irgsh.packager import Packager
from irgsh.builders.pbuilder import Pbuilder

from .conf import settings
from . import manager

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

        except IrgshException, e:
            self.retry([distribution, specification], kwargs, exc=e)

        finally:
            if logger is not None:
                logger.close()

    def _run(self, task_id, distribution, specification,
             resultdir, stdout, stderr):
        manager.update_status(task_id, manager.STARTED)

        # Create and prepare builder (pbuilder)
        pbuilder_path = settings.PBUILDER_PATH
        builder = Pbuilder(distribution, pbuilder_path)
        builder.init()
        if not os.path.exists(builder.configfile):
            builder.create()

        # Build package
        packager = Packager(specification, builder, resultdir,
                            stdout=stdout, stderr=stderr)
        packager.build()

    def on_success(self, retval, task_id, args, kwargs):
        manager.update_status(task_id, manager.SUCCESS)

        # TODO add package to (local) upload queue
        # TODO add log file to (local) upload queue

    def on_retry(self, exc, task_id, args, kwargs, einfo=None):
        manager.update_status(task_id, manager.RETRY)

        # TODO add log file to (local) upload queue

    def on_failure(self, task_id, args, kwargs, einfo=None):
        manager.update_status(task_id, manager.FAILURE)

        # TODO add log file to (local) upload queue

build_package = BuildPackage

