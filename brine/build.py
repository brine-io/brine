import json
import glob
import os
import codecs
from brine.dataset_manager import DatasetManager
from brine.builder import Builder
from brine.util import TemporaryDirectory, is_image_file
from brine.exceptions import BrineError


def build_config(dataset_name, config_file_path):
    dataset_manager = DatasetManager.get_from_dir(dataset_name, os.getcwd())
    dataset_manager.check_can_install()

    builder = Builder()
    with TemporaryDirectory() as temp_dir_path:
        builder.build_from_config(config_file_path, temp_dir_path)
        dataset_manager.create_from_dir(temp_dir_path)

    print('Dataset %s was built.' % dataset_name)


def build_data_dir(dataset_name, data_dir_path):
    file_paths = glob.glob(os.path.join(data_dir_path, '**', '*.*'), recursive=True)

    image_paths = list(filter(is_image_file, file_paths))
    image_paths = [os.path.relpath(image_path, data_dir_path) for image_path in image_paths]
    csv_file_path = os.path.join(data_dir_path, 'data.csv')
    config_file_path = os.path.join(data_dir_path, 'config.json')

    config = {
        'columns': [{
            'name': 'image',
            'type': 'image',
        }],
        'path': 'data.csv',
    }

    try:
        with codecs.open(config_file_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(config, indent=4))
    except IOError:
        raise BrineError('Could not create config file %s.' % config_file_path)

    try:
        with codecs.open(csv_file_path, 'w', encoding='utf-8') as f:
            f.write('image\n')
            for image_path in image_paths:
                f.write(image_path + '\n')
    except IOError:
        raise BrineError('Could not create csv file %s.' % csv_file_path)

    build_config(dataset_name, config_file_path)
