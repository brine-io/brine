import errno
import shutil
import tempfile


class TemporaryDirectory(object):

    def __init__(self):
        self.name = tempfile.mkdtemp()

    def __repr__(self):
        return "<{} {!r}>".format(self.__class__.__name__, self.name)

    def __enter__(self):
        return self.name

    def __exit__(self, exc, value, tb):
        try:
            shutil.rmtree(self.name)
        except OSError as ex:
            if ex.errno != errno.ENOENT:
                raise
