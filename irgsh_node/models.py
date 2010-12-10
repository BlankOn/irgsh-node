from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from irgsh_node.conf import settings

Base = declarative_base()

CT_RESULT = 0
CT_LOG = 1

class UploadQueue(Base):
    __tablename__ = 'irgsh_uploadqueue'
    __table_args__ = {'sqlite_autoincrement': True}

    id = sa.Column(sa.Integer, sa.Sequence("task_id_sequence"),
                   primary_key=True,
                   autoincrement=True)
    task_id = sa.Column(sa.String(255))

    content_type = sa.Column(sa.Integer, default=CT_RESULT)
    path = sa.Column(sa.String(255))
    is_absolute_path = sa.Column(sa.Boolean, default=False)

    created = sa.Column(sa.DateTime, default=datetime.now, nullable=True)
    updated = sa.Column(sa.DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=True)
    uploaded = sa.Column(sa.DateTime, default=None, nullable=True)

_session = None
def get_session():
    global _session
    if _session is None:
        engine = create_engine(settings.LOCAL_DATABASE, echo=True)
        Session = sessionmaker(bind=engine)
        _session = Session()
        Base.metadata.create_all(engine)
    return _session

