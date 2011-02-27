import os

def main():
    os.environ.setdefault('IRGSH_NODE_CONFIG', 'irgsh-node.conf')
    os.environ.setdefault('CELERY_LOADER', 'irgsh_node.loader.IrgshNodeLoader')

    from celery.bin import celeryd
    from celery.bin.celeryd import multiprocessing
    from irgsh_node.conf import settings

    class WorkerCommand(celeryd.WorkerCommand):
        def get_options(self):
            opts = super(WorkerCommand, self).get_options()
            for opt in opts:
                if opt.dest == 'hostname':
                    opt.default = settings.NODE_NAME
            return opts

    multiprocessing.freeze_support()
    worker = WorkerCommand()
    worker.execute_from_commandline()

if __name__ == '__main__':
    main()

