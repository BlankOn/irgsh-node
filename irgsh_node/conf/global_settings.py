CELERY_IMPORTS = ("irgsh_node.tasks", )

CELERY_RESULT_BACKEND = "database"
CELERY_RESULT_DBURI = "sqlite:///irgsh-node.db"

