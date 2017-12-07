from ethereum.db import BaseDB
import leveldb
import sys

PY3 = sys.version_info >= (3,)


class LevelDB(BaseDB):
    max_open_files = 32000
    # block_cache_size = 8 * 1024 ** 2
    # write_buffer_size = 4 * 1024 ** 2

    def __init__(self, dbfile):
        self.uncommitted = dict()
        self.dbfile = dbfile
        self.db = leveldb.LevelDB(dbfile, max_open_files=self.max_open_files)
        # self.commit_counter = 0

    def reopen(self):
        del self.db
        self.db = leveldb.LevelDB(self.dbfile)

    def get(self, key):
        if isinstance(key, str):
            key = key.encode()
        o = bytes(self.db.Get(key))
        return o
        # def get(self, key):
        #     if key in self.uncommitted:
        #         if self.uncommitted[key] is None:
        #             raise KeyError("key not in db")
        #         return self.uncommitted[key]
        #
        #     if PY3:
        #         if isinstance(key, str):
        #             key = key.encode()
        #         o = bytes(self.db.Get(key))
        #     else:
        #         o = decompress(self.db.Get(key))
        #     self.uncommitted[key] = o
        #     return o

        # def put(self, key, value):
        #     # log.trace('putting entry', key=encode_hex(key)[:8], len=len(value))
        #     self.uncommitted[key] = value
        #
        # def commit(self):
        #     # log.debug('committing', db=self)
        #     batch = leveldb.WriteBatch()
        #     for k, v in list(self.uncommitted.items()):
        #         if v is None:
        #             batch.Delete(k)
        #         else:
        #             # compress_v = compress(v)
        #             if PY3:
        #                 if isinstance(k, str):
        #                     k = k.encode()
        #                 if isinstance(compress_v, str):
        #                     compress_v = compress_v.encode()
        #             batch.Put(k, compress_v)
        #     self.db.Write(batch, sync=False)
        #     self.uncommitted.clear()
        # log.debug('committed', db=self, num=len(self.uncommitted))
        # self.commit_counter += 1
        # if self.commit_counter % 100 == 0:
        #     self.reopen()

    # def delete(self, key):
    #     # log.trace('deleting entry', key=key)
    #     self.uncommitted[key] = None

    def _has_key(self, key):
        try:
            self.get(key)
            return True
        except KeyError:
            return False
        except Exception as e:
            # log.info('key: {}, type(key):{}'.format(key, type(key)))
            raise

    def __contains__(self, key):
        return self._has_key(key)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.db == other.db

    def __repr__(self):
        return '<DB at %d uncommitted=%d>' % (id(self.db), len(self.uncommitted))

    # def inc_refcount(self, key, value):
    #     self.put(key, value)

    # def dec_refcount(self, key):
    #     pass

    # def revert_refcount_changes(self, epoch):
    #     pass

    # def commit_refcount_changes(self, epoch):
    #     pass

    # def cleanup(self, epoch):
    #     pass

        # def put_temporarily(self, key, value):
        #     self.inc_refcount(key, value)
        #     self.dec_refcount(key)
