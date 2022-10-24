import tarfile
import requests
from tqdm import tqdm

from brine.exceptions import BrineError


def download_and_extract(signed_url, destination_dir_path):
    try:
        _download_and_extract(signed_url, destination_dir_path)
    except requests.exceptions.RequestException:
        raise DownloadError('Unable to reach server. Please try again later.')
    except tarfile.TarError:
        raise DownloadError('Failed to extract file %s.' % destination_dir_path)


def _download_and_extract(signed_url, destination_dir_path):
    r = requests.get(signed_url, stream=True)
    r.raise_for_status()

    try:
        content_length = int(r.headers.get('Content-Length'))
    except (ValueError, TypeError):
        content_length = 0
    download_progress = DownloadProgress(r.raw, total=content_length)
    with tarfile.open(fileobj=download_progress, mode='r|') as tar:
        
        import os
        
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tar, path=destination_dir_path)


class DownloadError(BrineError):
    pass


class DownloadProgress(object):

    def __init__(self, fileobj, total):
        self.fileobj = fileobj
        self.progress_bar = tqdm(unit='B', unit_scale=True, total=total)

    def read(self, size=-1):
        data = self.fileobj.read(size)
        self.progress_bar.update(len(data))
        return data
