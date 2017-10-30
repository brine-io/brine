import codecs
import errno
import glob
import json
import os
import shutil
import re

from brine.env import Env
from brine.exceptions import BrineError


# (?!.*--): cannot contain '--'
# (?!-): cannot start with '-'
# (?<!-): cannot end with '-'
NAME_REGEX = re.compile(r'^(?!.*--)(?!-)([A-Za-z0-9-]+)(?<!-)/(?!-)([A-Za-z0-9-]+)(?<!-)$')


class DatasetManager(object):

    def __init__(self, name, path):
        self.name = name
        self.parse_name(name)
        self.path = os.path.abspath(path)
        self.hidden_file_path = os.path.join(self.path, Env.HIDDEN_FILE_NAME)

    @classmethod
    def list_in_dir(cls, path):
        files = glob.glob(os.path.join(path, Env.DATASETS_DIR_NAME, '*/*', Env.HIDDEN_FILE_NAME))
        files = filter(os.path.isfile, files)
        paths = list(map(os.path.dirname, files))
        names = list(map(lambda p: os.path.relpath(p, start=os.path.join(path, Env.DATASETS_DIR_NAME)), paths))
        dataset_managers = []
        for name, path in zip(names, paths):
            try:
                dataset_manager = cls(name, path)
            except DatasetManagerError:
                continue
            dataset_managers.append(dataset_manager)
        return dataset_managers

    @classmethod
    def get_from_dir(cls, name, path):
        (scope, name_without_scope) = cls.parse_name(name)
        return cls(name, os.path.join(path, Env.DATASETS_DIR_NAME, scope, name_without_scope))

    @staticmethod
    def parse_name(name):
        m = NAME_REGEX.match(name)
        if m is None:
            raise DatasetManagerError('Dataset name %s is not valid.' % name)
        return m.groups()

    def exists(self):
        return os.path.exists(self.hidden_file_path)

    def version(self):
        hidden_file_obj = self._load_hidden_file()
        return hidden_file_obj.get('version')

    def set_version(self, version):
        hidden_file_obj = self._load_hidden_file()
        current_version = hidden_file_obj.get('version')
        if current_version is not None:
            raise DatasetManagerError('Cannot set version on dataset %s.' % self.name)
        hidden_file_obj['version'] = version
        self._save_hidden_file(hidden_file_obj)

    def _load_hidden_file(self):
        try:
            with codecs.open(self.hidden_file_path, 'r', encoding='utf-8') as f:
                return json.loads(f.read())
        except (IOError, ValueError):
            return {}

    def _save_hidden_file(self, hidden_file_obj):
        try:
            with codecs.open(self.hidden_file_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(hidden_file_obj))
        except (IOError, ValueError):
            raise DatasetManagerError('Could not save file %s' % self.hidden_file_path)

    def remove(self):
        if not self.exists():
            raise DatasetManagerError('Dataset %s is not installed.' % self.name)
        try:
            shutil.rmtree(self.path)
        except OSError as ex:
            if ex.errno != errno.ENOENT:
                raise DatasetManagerError('Dataset %s could not be removed.' % self.name)

    def check_can_install(self):
        if self.exists():
            raise DatasetManagerError('Dataset %s is already installed.' % self.name)

        if os.path.exists(self.path):
            raise DatasetManagerError('Dataset %s directory could not be created at %s.' % (self.name, self.path))

        p = self.path
        while not os.path.exists(p):
            p = os.path.dirname(p)

        if not os.path.isdir(p) or not os.access(p, os.R_OK | os.W_OK | os.F_OK):
            raise DatasetManagerError('Dataset %s directory could not be created at %s.' % (self.name, self.path))

    def check_can_push(self):
        if not self.exists():
            raise DatasetManagerError('Dataset %s has not been built.' % self.name)

        if self.version() is not None:
            raise DatasetManagerError('Dataset %s has already been pushed.' % self.name)

    def create_from_dir(self, source_path, version=None):
        if self.exists():
            raise DatasetManagerError('Dataset %s is already installed.' % self.name)

        dataset_manager = DatasetManager(self.name, source_path)
        dataset_manager.set_version(version)

        path_parent = os.path.dirname(self.path)
        try:
            os.makedirs(path_parent)
        except OSError as ex:
            if ex.errno != errno.EEXIST or not os.path.isdir(path_parent):
                raise DatasetManagerError('Dataset %s directory could not be created at %s.' % (self.name, self.path))

        try:
            shutil.move(source_path, self.path)
        except OSError as ex:
            raise DatasetManagerError('Dataset %s directory could not be created from %s.' % (self.name, source_path))


class DatasetManagerError(BrineError):
    pass
