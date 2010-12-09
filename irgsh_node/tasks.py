import os

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
        try:
            self._run(distribution, specification, **kwargs)
        except IrgshException, e:
            self.retry([distribution, specification], kwargs, exc=e)

    def _run(self, distribution, specification, **kwargs):
        task_id = kwargs['task_id']
        manager.update_status(task_id, manager.STARTED)

        # Create and prepare builder (pbuilder)
        pbuilder_path = settings.PBUILDER_PATH
        resultdir = os.path.join(settings.RESULT_DIR, task_id)
        if not os.path.exists(resultdir):
            os.makedirs(resultdir)

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

    def on_retry(self, exc, task_id, args, kwargs, einfo=None):
        manager.update_status(task_id, manager.RETRY)

    def on_failure(self, task_id, args, kwargs, einfo=None):
        manager.update_status(task_id, manager.FAILURE)

build_package = BuildPackage

