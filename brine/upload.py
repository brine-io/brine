import codecs
import hashlib
import os
import re
import requests
from tqdm import tqdm

from brine.exceptions import BrineError


RETRY_STATUS_CODES = [408, 429, 500, 502, 503, 504]
BUFFER_SIZE = 8192


def upload(signed_url, source_file_path):
    session_url = _get_session_url(signed_url)

    try:
        with codecs.open(source_file_path, 'rb') as f:
            f.seek(0, os.SEEK_END)
            file_length = f.tell()
            upload_progress = UploadProgress(total=file_length)
            while not _upload_attempt(session_url, f, file_length, upload_progress):
                pass
    except IOError:
        raise UploadError('Failed to upload file to server.')


def _get_session_url(signed_url):
    r = requests.post(signed_url, headers={
        'Content-Length': '0',
        'Content-Type': 'application/octet-stream',
        'x-goog-resumable': 'start',
    })
    if r.status_code != 201:
        raise UploadError('Failed to create a signed upload URL.')
    return r.headers['Location']


def _upload_attempt(session_url, f, file_length, upload_progress):
    try:
        r = requests.put(session_url, headers={
            'Content-Length': '0',
            'Content-Range': 'bytes */%d' % file_length,
        })
    except requests.RequestException:
        return False

    if r.status_code in RETRY_STATUS_CODES:
        return False
    elif r.status_code in (200, 201):
        # handle edge case for file upload already completed
        etag = r.headers['ETag'].strip('"')
        if etag != upload_progress.md5.hexdigest():
            raise UploadError('Failed to upload file to server.')
        return True
    elif r.status_code != 308:
        raise UploadError('Failed to upload file to server.')

    if 'Range' not in r.headers:
        uploaded_range = (0, 0)
        headers = {}
    else:
        # this byte range header is inclusive, so bytes=(0, 0) means that one byte is uploaded
        m = re.search(r'bytes=(\d+)-(\d+)', r.headers['Range'])
        # convert to exclusive range
        uploaded_range = (int(m.group(1)), int(m.group(2)) + 1)
        headers = {
            'Content-Range': 'bytes %d-%d/%d' % (
                uploaded_range[1],
                file_length - 1,
                file_length,
            )
        }
    try:
        r = requests.put(
            session_url,
            headers=headers,
            data=upload_progress.read(f, uploaded_range[1])
        )
    except requests.RequestException:
        return False

    if r.status_code in RETRY_STATUS_CODES:
        return False
    elif r.status_code in (200, 201):
        etag = r.headers['ETag'].strip('"')
        if etag != upload_progress.md5.hexdigest():
            raise UploadError('Failed to upload file to server.')
        return True
    else:
        raise UploadError('Failed to upload file to server.')


class UploadProgress(object):

    def __init__(self, total):
        self.offset = 0
        self.md5 = hashlib.md5()
        self.progress_bar = tqdm(unit='B', unit_scale=True, total=total)

    def read(self, f, offset):
        f.seek(offset)
        while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                return
            self.update(chunk, offset)
            offset += len(chunk)
            yield chunk

    def update(self, chunk, offset):
        if self.offset >= len(chunk) + offset:
            return
        new_chunk = chunk[self.offset - offset:]
        self.md5.update(new_chunk)
        self.progress_bar.update(len(new_chunk))
        self.offset = len(chunk) + offset


class UploadError(BrineError):
    pass
