from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from irgsh_node.conf import settings

Base = declarative_base()

class UploadQueue(Base):
    __tablename__ = 'irgsh_uploadqueue'
    __table_args__ = {'sqlite_autoincrement': True}

    id = sa.Column(sa.Integer, sa.Sequence("task_id_sequence"),
                   primary_key=True,
                   autoincrement=True)
    task_id = sa.Column(sa.String(255))
    created = sa.Column(sa.DateTime, default=datetime.now, nullable=True)
    updated = sa.Column(sa.DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=True)
    uploaded = sa.Column(sa.DateTime, default=None, nullable=True)

    filename = sa.Column(sa.String(255))
    absolute_path = sa.Column(sa.Boolean, default=False)

_session = None
def get_session():
    global _session
    if _session is None:
        engine = create_engine(settings.LOCAL_DATABASE, echo=True)
        Session = sessionmaker(bind=engine)
        _session = Session()
        Base.metadata.create_all(engine)
    return _session

