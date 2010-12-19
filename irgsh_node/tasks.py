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
            metadir = os.path.join(taskdir, 'meta')
            for dirname in [logdir, resultdir, metadir]:
                if not os.path.exists(dirname):
                    os.makedirs(dirname)

            # Prepare logger
            logname = os.path.join(logdir, 'log.%d.gz' % retries)
            logger = gzip.GzipFile(logname, 'wb')
            stdout = stderr = logger

            # Execute builder
            self._run(task_id, taskdir, distribution, specification,
                      resultdir, stdout, stderr, kwargs)

        finally:
            if logger is not None:
                logger.close()
                self.upload_log(task_id, retries)

    def _run(self, task_id, taskdir, distribution, specification,
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
        try:
            work_dir = tempfile.mkdtemp('-irgsh-builder')
            dsc_dir = os.path.join(work_dir, 'dsc')
            source_dir = os.path.join(work_dir, 'source')
            orig_path = None

            packager.export_source(source_dir)
            self.upload_control_file(task_id, taskdir, source_dir)

            orig_path = packager.retrieve_orig()
            dsc = packager.generate_dsc(dsc_dir, source_dir, orig_path)
            dsc_path = os.path.join(dsc_dir, dsc)
            packager.build_package(dsc_path)

        finally:
            shutil.rmtree(work_dir)
            if orig_path is not None:
                os.unlink(orig_path)

    def on_success(self, retval, task_id, args, kwargs):
        distribution, specification = args

        self.update_status(task_id, manager.SUCCESS)
        self.upload_package(task_id, args[0], retval)

        clog = self.get_logger(**kwargs)
        clog.info('Package %s for %s built successfully' % \
                  (specification.location, distribution.name))

    def on_retry(self, exc, task_id, args, kwargs, einfo=None):
        distribution, specification = args

        self.update_status(task_id, manager.RETRY)

        clog = self.get_logger(**kwargs)
        clog.info('Package %s for %s failed to build, retrying..' % \
                  (specification.location, distribution.name))

    def on_failure(self, exc, task_id, args, kwargs, einfo=None):
        distribution, specification = args

        self.update_status(task_id, manager.FAILURE)

        clog = self.get_logger(**kwargs)
        clog.info('Package %s for %s failed to build' % \
                  (specification.location, distribution.name))

    def upload_control_file(self, task_id, taskdir, source_dir):
        dirname = find_changelog(source_dir)
        if dirname is None:
            raise ValueError('Unable to find debian/control')

        control = os.path.join(dirname, 'debian', 'control')
        if not os.path.exists(control):
            raise ValueError('Unable to find debian/control')

        path = 'meta/control'
        shutil.copy(control, os.path.join(taskdir, path)

        self.upload(task_id, path, consts.TYPE_CONTROL)

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

