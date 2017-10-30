import tarfile
import os

from brine.env import Env
from brine.exceptions import BrineError


def archive(source_dir_path, tar_file_path):
    try:
        with tarfile.open(tar_file_path, 'w') as tar:
            tar.add(
                source_dir_path,
                arcname=os.path.sep,
                filter=lambda tarinfo: None if tarinfo.name == Env.HIDDEN_FILE_NAME else tarinfo)
    except tarfile.TarError:
        raise ArchiveError('Failed to archive file %s.' % tar_file_path)


class ArchiveError(BrineError):
    pass
