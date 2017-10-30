import os
from brine.dataset_manager import DatasetManager


def uninstall(dataset_name):
    dataset_manager = DatasetManager.get_from_dir(dataset_name, os.getcwd())
    version = dataset_manager.version()
    dataset_manager.remove()

    print('Dataset %s (v%s) was uninstalled.' % (dataset_name, version))
