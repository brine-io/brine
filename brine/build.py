import os
from brine.dataset_manager import DatasetManager
from brine.builder import Builder
from brine.util import TemporaryDirectory


def build(dataset_name, config_file_path):
    dataset_manager = DatasetManager.get_from_dir(dataset_name, os.getcwd())
    dataset_manager.check_can_install()

    builder = Builder()
    with TemporaryDirectory() as temp_dir_path:
        builder.build_from_config(config_file_path, temp_dir_path)
        dataset_manager.create_from_dir(temp_dir_path)

    print('Dataset %s was built.' % dataset_name)
