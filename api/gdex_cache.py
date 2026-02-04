from django.core.cache.backends.filebased import FileBasedCache
import urllib
import os


class GDEX_FileBasedCache(FileBasedCache):

    def _key_to_file(self, key, version=None):
        """
        Convert a key into a cache file path. Basically this is the
        root cache path joined with the md5sum of the key and a suffix.
        """
        key = self.make_and_validate_key(key, version=version)
        return os.path.join(
                self._dir,
                "".join(
                    [
                        key.replace('/','-'),
                        #md5(key.encode(), usedforsecurity=False).hexdigest(),
                        self.cache_suffix,
                    ]
                ),
            )
