import os
from brine.api import get_version_for_install
from brine.dataset_manager import DatasetManager
from brine.download import download_and_extract
from brine.util import TemporaryDirectory


def install(dataset_name):
    dataset_manager = DatasetManager.get_from_dir(dataset_name, os.getcwd())
    dataset_manager.check_can_install()

    response = get_version_for_install(dataset_name)

    with TemporaryDirectory() as temp_dir_path:
        download_and_extract(response['signed_url'], temp_dir_path)
        dataset_manager.create_from_dir(temp_dir_path, response['version_number'])

    print('Dataset %s (v%s) was installed.' % (dataset_name, dataset_manager.version()))
