import os
import gzip
from datetime import timedelta
import tempfile
import shutil

from celery.task import Task, PeriodicTask

from irgsh.error import IrgshException
from irgsh.packager import Packager
from irgsh.builders.pbuilder import Pbuilder
from irgsh.utils import find_changelog

from irgsh_node.conf import settings
from irgsh_node import manager, consts

class TaskCancelled(Exception):
    pass

class BuildPackage(Task):
    exchange = 'builder'
    ignore_result = True

    max_retries = 5
    default_retry_delay = 5 * 60

    def run(self, spec_id, specification, distribution, **kwargs):
        logger = None

        try:
            task_id = kwargs['task_id']
            retries = kwargs['task_retries']

            # Check latest status
            self.check_spec_status(spec_id)

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
            logname = os.path.join(logdir, 'log.%d.gz' % retries)
            logger = gzip.GzipFile(logname, 'wb')
            stdout = stderr = logger

            # Execute builder
            self._run(spec_id, task_id, taskdir, distribution, specification,
                      resultdir, stdout, stderr, kwargs)

        except TaskCancelled, e:
            self.update_status(task_id, manager.CANCELLED)

        finally:
            if logger is not None:
                logger.close()
                self.upload_log(task_id, retries)

    def _run(self, spec_id, task_id, taskdir, distribution, specification,
             resultdir, stdout, stderr, kwargs):
        clog = self.get_logger(**kwargs)

        # Create and prepare builder (pbuilder)
        pbuilder_path = settings.PBUILDER_PATH
        builder = Pbuilder(distribution, pbuilder_path)

        # Build package
        clog.info('Building package %s for %s' % (specification.location,
                                                  distribution.name))
        packager = Packager(specification, builder, resultdir,
                            stdout=stdout, stderr=stderr)
        try:
            work_dir = tempfile.mkdtemp('-irgsh-builder')
            dsc_dir = os.path.join(work_dir, 'dsc')
            source_dir = os.path.join(work_dir, 'source')
            for path in [dsc_dir, source_dir]:
                os.makedirs(path)
            orig_path = None

            self.update_status(task_id, manager.DOWNLOADING_SOURCE)
            packager.export_source(source_dir)

            self.check_spec_status(spec_id)

            self.update_status(task_id, manager.DOWNLOADING_ORIG)
            orig_path = packager.retrieve_orig()

            self.check_spec_status(spec_id)

            self.update_status(task_id, manager.BUILDING)
            dsc = packager.generate_dsc(dsc_dir, source_dir, orig_path)
            dsc_path = os.path.join(dsc_dir, dsc)
            changes = packager.build_package(dsc_path)

            self.upload_package(task_id, distribution, changes)
        finally:
            shutil.rmtree(work_dir)
            if orig_path is not None:
                os.unlink(orig_path)

    def on_success(self, retval, task_id, args, kwargs):
        spec_id, specification, distribution = args

        self.update_status(task_id, manager.BUILT)

        clog = self.get_logger(**kwargs)
        clog.info('Package built successfully')

    def on_retry(self, exc, task_id, args, kwargs, einfo=None):
        spec_id, specification, distribution = args

        self.update_status(task_id, manager.FAILED)

        clog = self.get_logger(**kwargs)
        clog.info('Package failed to build, retrying..')

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

    def upload_log(self, task_id, index):
        self.upload(task_id, 'logs/log.%s.gz' % index, consts.TYPE_LOG)

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

