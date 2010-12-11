import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from irgsh_node.conf import settings

Base = declarative_base()

class LocalQueue(Base):
    __tablename__ = 'localqueue_queue'
    __table_args__ = {'sqlite_autoincrement': True}

    id = sa.Column(sa.Integer, sa.Sequence("queue_id_sequence"),
                   primary_key=True,
                   autoincrement=True)

    created = sa.Column(sa.DateTime, default=datetime.now, nullable=True)
    updated = sa.Column(sa.DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=True)
    payload = sa.Column(sa.PickleType, default=None)

    fetched = sa.Column(sa.Boolean, default=False)

_sessions = {}
def get_session(uri):
    session = _sessions.get(uri, None)
    if session is None:
        engine = create_engine(uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        Base.metadata.create_all(engine)
        _sessions[uri] = session
    return session

