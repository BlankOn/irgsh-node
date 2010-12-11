from datetime import datetime

from .models import get_session, LocalQueue, FetchedItem

class Queue(object):
    def __init__(self, uri):
        self.uri = uri
        self._session = None

    @property
    def session(self):
        if self._session is None:
            self._sessions = get_session(self.uri)
        return self._session

    def put(self, content):
        item = LocalQueue()
        item.payload = content

        session = self.session
        session.add(item)
        session.commit()

    def get(self):
        session = self.session

        items = session.query(LocalQueue) \
                       .filter(LocalQueue.fetched==False) \
                       .order_by(LocalQueue.updated) \
                       .values(LocalQueue.id)

        qid = None
        for item_id in [item[0] for item in items]:
            total = session.query(LocalQueue) \
                           .filter(LocalQueue.id==item_id) \
                           .filter(LocalQueue.fetched==False) \
                           .update({LocalQueue.fetched: True})
            session.commit()
            if total > 0:
                qid = item_id
                break

        if qid is None:
            return None

        item = session.query(LocalQueue) \
                      .filter(LocalQueue.id==qid) \
                      .one()
        item.updated = datetime.now()
        session.add(item)
        session.commit()

        return item

    def remove(self, item):
        session = self.session
        session.delete(item)
        session.commit()

    def reset(self, item, increment=True):
        item.fetched = False
        if increment:
            item.counter += 1

        session = self.session
        session.add(item)
        session.commit()

