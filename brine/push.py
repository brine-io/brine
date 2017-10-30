import os
from brine.api import create_upload_session, get_upload_session_signed_url, complete_upload_session, ApiError
from brine.dataset_manager import DatasetManager, DatasetManagerError
from brine.util import TemporaryDirectory
from brine.upload import upload, UploadError
from brine.archive import archive, ArchiveError


def push(dataset_name):
    dataset_manager = DatasetManager.get_from_dir(dataset_name, os.getcwd())
    dataset_manager.check_can_push()

    response = create_upload_session(dataset_name)
    upload_session_id = response['upload_session_id']

    with TemporaryDirectory() as temp_dir_path:

        tar_file_path = os.path.join(temp_dir_path, 'dataset.tar')

        archive(dataset_manager.path, tar_file_path)

        response = get_upload_session_signed_url(upload_session_id, 'dataset.tar')
        signed_url = response['signed_url']

        upload(signed_url, tar_file_path)

    response = complete_upload_session(upload_session_id)
    dataset_manager.set_version(response['version_number'])

    print('Dataset %s (v%s) was pushed.' % (dataset_manager.name, dataset_manager.version()))
