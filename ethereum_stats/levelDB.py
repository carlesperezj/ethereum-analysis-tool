import leveldb

from ethereum.db import BaseDB


class LevelDB(BaseDB):
    max_open_files = 32000

    def __init__(self, dbfile):
        self.uncommitted = dict()
        self.dbfile = dbfile
        self.db = leveldb.LevelDB(dbfile, max_open_files=self.max_open_files)

    def reopen(self):
        del self.db
        self.db = leveldb.LevelDB(self.dbfile)

    def get(self, key):
        if isinstance(key, str):
            key = key.encode()
        o = bytes(self.db.Get(key))
        return o

    def _has_key(self, key):
        try:
            self.get(key)
            return True
        except KeyError:
            return False
        except Exception as e:
            raise

    def __contains__(self, key):
        return self._has_key(key)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.db == other.db

    def __repr__(self):
        return '<DB at %d uncommitted=%d>' % (id(self.db), len(self.uncommitted))

