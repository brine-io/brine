import codecs
import errno
import shutil
import os
import json
from tqdm import tqdm
import bcolz
import pandas
import numpy as np

from brine.exceptions import BrineError
from brine.schema import Schema, Integer, Float, Category, String, Image, IntegerArray, FloatArray, CategoryArray


class Builder(object):

    def build_from_config(self, config_file_path, destination_dir_path):

        try:
            with codecs.open(config_file_path, 'r', encoding='utf-8') as f:
                config = json.loads(f.read())
                config_columns = config['columns']
                config_path = config['path']
                config_extra_data = config.get('extra_data') or None
        except (IOError, ValueError, KeyError):
            raise BuilderError

        dtype = {}
        converters = {}
        num_image_columns = 0
        for config_column in config_columns:
            name = config_column['name']
            column_type = config_column['type']
            if column_type == 'integer':
                dtype[name] = np.int64
            elif column_type == 'float':
                dtype[name] = np.float
            elif column_type == 'category':
                converter = CategoryConverter()
                converters[name] = converter
            elif column_type == 'string':
                dtype[name] = np.unicode
            elif column_type == 'image':
                dtype[name] = np.unicode
                num_image_columns = num_image_columns + 1
            elif column_type == 'integer_array':
                converter = ArrayConverter(np.int64)
                converters[name] = converter
            elif column_type == 'float_array':
                converter = ArrayConverter(np.float)
                converters[name] = converter
            elif column_type == 'category_array':
                converter = ArrayConverter(CategoryConverter())
                converters[name] = converter

        csv_file_path = os.path.join(os.path.dirname(config_file_path), config_path)
        try:
            df = pandas.read_csv(csv_file_path, dtype=dtype, converters=converters)
        except IOError:
            raise BuilderError
        df = df.reindex(columns=[config_column['name'] for config_column in config_columns])
        progress_bar = tqdm(unit=' images', total=num_image_columns * df.shape[0])

        schema = Schema()
        for config_column in config_columns:
            name = config_column['name']
            column_type = config_column['type']
            if column_type == 'integer':
                schema.add_column(name, Integer())
            elif column_type == 'float':
                schema.add_column(name, Float())
            elif column_type == 'category':
                schema.add_column(name, Category(converters[name].categories))
            elif column_type == 'string':
                schema.add_column(name, String())
            elif column_type == 'image':
                schema.add_column(name, Image())
                for file_path in df[name]:
                    self.copy_image_file(file_path, os.path.dirname(config_file_path), destination_dir_path)
                    progress_bar.update(1)
            elif column_type == 'integer_array':
                schema.add_column(name, IntegerArray())
            elif column_type == 'float_array':
                schema.add_column(name, FloatArray())
            elif column_type == 'category_array':
                schema.add_column(name, CategoryArray(converters[name].items_converter.categories))

        ctable = bcolz.ctable.fromdataframe(df, rootdir=os.path.join(destination_dir_path, 'bcolz'))
        ctable.attrs['extra_data'] = json.dumps(config_extra_data)
        ctable.attrs['schema'] = json.dumps(schema.to_obj())
        ctable.flush()

    def copy_image_file(self, file_path, src_dir_path, dst_dir_path):
        src_file_path = os.path.join(src_dir_path, file_path)
        dst_file_path = os.path.join(dst_dir_path, 'images', file_path)
        if not os.path.abspath(dst_file_path).startswith(dst_dir_path):
            raise BuilderError
        try:
            shutil.copyfile(src_file_path, dst_file_path)
        except IOError as ex:
            if ex.errno != errno.ENOENT:
                raise BuilderError
            try:
                os.makedirs(os.path.dirname(dst_file_path))
                shutil.copyfile(src_file_path, dst_file_path)
            except IOError:
                raise BuilderError


class BuilderError(BrineError):
    pass


class CategoryConverter(object):

    def __init__(self):
        self.categories_dict = {}

    def __call__(self, value):
        if value not in self.categories_dict:
            self.categories_dict[value] = len(self.categories_dict)
        return self.categories_dict[value]

    @property
    def categories(self):
        return list(self.categories_dict)


class ArrayConverter(object):

    def __init__(self, items_converter):
        self.items_converter = items_converter

    def __call__(self, value):
        return [self.items_converter(x) for x in value.split(' ')]
