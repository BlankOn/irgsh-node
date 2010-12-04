from celery.loaders.base import BaseLoader

class IrgshNodeLoader(BaseLoader):
    def read_configuration(self):
        from irgsh_node.conf import settings
        self.configured = True
        return settings

