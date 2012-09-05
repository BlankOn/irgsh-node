import os
import gzip
from datetime import timedelta
import tempfile
import shutil

from celery.task import Task, PeriodicTask

from irgsh.packager import Packager
from irgsh.builders.pbuilder import Pbuilder

from irgsh_node.conf import settings
from irgsh_node import manager, consts

class TaskCancelled(Exception):
    pass

class BuildPackage(Task):
    exchange = 'builder'
    ignore_result = True

    def run(self, spec_id, specification, distribution, **kwargs):
        logger = None

        try:
            task_id = self.request.id

            # Check latest status
            self.check_spec_status(spec_id)

            # Try to claim task
            self.claim(task_id)

            # Prepare directories
            self.update_status(task_id, manager.PREPARING)

            taskdir = os.path.join(settings.RESULT_DIR, task_id)
            logdir = os.path.join(taskdir, 'logs')
            resultdir = os.path.join(taskdir, 'result')
            metadir = os.path.join(taskdir, 'meta')
            for dirname in [logdir, resultdir, metadir]:
                if not os.path.exists(dirname):
                    os.makedirs(dirname)

            # Prepare logger
            logname = os.path.join(logdir, 'build.log')
            logger = open(logname, 'wb')

            # Execute builder
            self._run(spec_id, task_id, taskdir, distribution, specification,
                      resultdir, logger, kwargs)

        except TaskCancelled, e:
            self.update_status(task_id, manager.CANCELLED)

        finally:
            if logger is not None:
                logger.close()

                logger = open(logname, 'rb')
                gzlogname = os.path.join(logdir, 'build.log.gz')
                gz = gzip.open(gzlogname, 'wb')
                gz.write(logger.read())
                gz.close()
                logger.close()

                os.unlink(logname)

                self.upload_log(task_id)

    def _run(self, spec_id, task_id, taskdir, distribution, specification,
             resultdir, logger, kwargs):
        clog = self.get_logger(**kwargs)

        # Create and prepare builder (pbuilder)
        pbuilder_path = settings.PBUILDER_PATH
        pbuilder_debootstrap = settings.PBUILDER_DEBOOTSTRAP

        keyring = os.path.abspath(settings.KEYRING)
        builder = Pbuilder(distribution, pbuilder_path, keyring=keyring,
                           debootstrap=pbuilder_debootstrap)

        # Build package
        clog.info('Building package %s for %s' % (specification.source,
                                                  distribution.name))

        self.update_status(task_id, manager.BUILDING)
        packager = Packager(specification, builder)
        changes = packager.build(resultdir, logger)

        self.upload_package(task_id, distribution, changes)

    def on_success(self, retval, task_id, args, kwargs):
        spec_id, specification, distribution = args

        self.update_status(task_id, manager.BUILT)

        clog = self.get_logger(**kwargs)
        clog.info('Package built successfully')

    def on_failure(self, exc, task_id, args, kwargs, einfo=None):
        spec_id, specification, distribution = args

        self.update_status(task_id, manager.FAILED)

        clog = self.get_logger(**kwargs)
        clog.info('Package failed to build')

    def upload_package(self, task_id, distribution, changes):
        extra = {'distribution': {'name': distribution.name,
                                  'mirror': distribution.mirror,
                                  'dist': distribution.dist,
                                  'components': distribution.components,
                                  'extra': distribution.extra}}

        self.upload(task_id, 'result/%s' % changes, consts.TYPE_RESULT, extra)

    def update_status(self, task_id, status):
        try:
            manager.update_status(task_id, status)
        except IOError:
            pass

    def upload_log(self, task_id):
        self.upload(task_id, 'logs/build.log.gz', consts.TYPE_LOG)

    def upload(self, task_id, path, content_type, extra={}):
        from irgsh_node.localqueue import Queue

        data = {}
        data.update(extra)
        data.update({'task_id': task_id,
                     'path': path,
                     'content_type': content_type})

        queue = Queue(settings.LOCAL_DATABASE)
        queue.put(data)

    def check_spec_status(self, spec_id):
        res = manager.get_spec_status(spec_id)
        if res['code'] < 0:
            raise TaskCancelled()
        return True

    def claim(self, task_id):
        res = manager.claim_task(task_id)
        if res['code'] < 0:
            raise TaskCancelled()
        return True

