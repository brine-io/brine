import os
from brine.dataset_manager import DatasetManager


def ls():
    for dataset_manager in DatasetManager.list_in_dir(os.getcwd()):
        version = dataset_manager.version()
        if version is None:
            print('%s (local)' % dataset_manager.name)
        else:
            print('%s (v%s)' % (dataset_manager.name, version))
