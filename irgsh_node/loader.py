from celery.loaders.base import BaseLoader
from celery.datastructures import DictAttribute

class IrgshNodeLoader(BaseLoader):
    def read_configuration(self):
        from irgsh_node.conf import settings
        self.configured = True
        return DictAttribute(settings)

    def on_worker_init(self):
        self.import_default_modules()

