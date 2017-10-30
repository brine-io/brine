import json
import random
import itertools
import os
from collections import namedtuple
from PIL import Image
import bcolz

from brine.schema import Schema
from brine.dataset_manager import DatasetManager
from brine.exceptions import BrineError


def load_dataset(dataset_name, base_path=None):
    """Load a brine dataset that has been installed with `brine install`.

    Parameters
    ----------
    dataset_name : str
        The full name of the dataset to load (eg. examples/cifar10)
    base_path : str
        The path where the dataset was installed. If None, defaults to the current working directory.
    Returns
    -------
    :class:`~brine.dataset.Dataset`
    """
    dataset_manager = DatasetManager.get_from_dir(dataset_name, base_path or os.getcwd())
    return Dataset(dataset_manager)


class Dataset(object):
    """A class to load and interface with a brine dataset

    Use this to get rows from the dataset, create training and validation folds and load images.
    This class also provides methods to create PyTorch and Keras compatible datasets and generators.

    For most cases, use the :func:`~brine.load_dataset` convenience method to load a dataset and return
    a Dataset.
    """

    def __init__(self, dataset_manager, indices=None):
        """
        Parameters
        ----------
        dataset : Dataset
            A brine.Dataset representing the dataset to load.
        indices : list of int
            The indices of the original dataset to use for this dataset. Used for creating folds.
        """
        self.dataset_manager = dataset_manager
        self.indices = indices

        try:
            self.metadata = bcolz.open(os.path.join(self.dataset_manager.path, 'bcolz'), mode='r')
        except IOError:
            raise DatasetError('Dataset %s could not be loaded.' % self.dataset_manager.name)

        self.schema = Schema.from_obj(json.loads(self.metadata.attrs['schema']))
        self.converters = {}
        for i, column in enumerate(self.schema.columns):
            if column.categories:
                if column.isarray():
                    converter = ArrayConverter(CategoryConverter(column.categories))
                    self.converters[i] = converter
                else:
                    converter = CategoryConverter(column.categories)
                    self.converters[i] = converter

        self.extra_data = json.loads(self.metadata.attrs['extra_data'])
        self.Row = namedtuple('Row', [column.name for column in self.schema.columns])
        self.Column = namedtuple('Column', [column.name for column in self.schema.columns])

    def __repr__(self):
        return 'Dataset(name=%s, path=%s)' % (self.dataset_manager.name, self.dataset_manager.path)

    def create_folds(self, fold_sizes, shuffle=False):
        """Returns sub-datasets from this dataset. Useful for creating training and validation folds.

        Parameters
        ----------
        fold_sizes : list of int
            Sizes of the folds to create.
        shuffle : bool
            Whether to shuffle the dataset before creating folds. Defaults to False.

        Returns
        -------
        list of Dataset
            A list of size len(fold_sizes) + 1 of Dataset for the sub-datasets created.
            Any rows leftover will always be returned in the last element of the list as a Dataset.
        """
        total = sum(fold_sizes)
        if total > len(self):
            raise DatasetError
        if self.indices is not None:
            indices = self.indices
        else:
            indices = list(range(0, len(self)))
        if shuffle:
            indices = random.sample(indices, len(self))
        iterator = iter(indices)
        slices = [s for s in (list(itertools.islice(iterator, 0, i)) for i in fold_sizes)]
        remaining = list(iterator)
        slices.append(remaining)
        folds = [Dataset(self.dataset_manager, indices=s) for s in slices]
        return folds

    def to_keras(self, x_column, y_column=None, batch_size=32, processing_function=None, shuffle=True, seed=None):
        """Creates a generator that can be used with Keras' fit_generator.

        Parameters
        ----------
        x_column : str
            The name of the column to treat as the 'x' value
        y_column : str
            The name of the column to treat as the 'y' value. Defaults to None.
        batch_size : int
            The batch size. Defaults to 32.
        processing_function
            Function to apply to each row before it's returned from the generator.
            The function is passed a tuple (x, y) and is expected to return
            (processed_x, processed_y). Images will automatically be converted to numpy arrays
            using Keras' img_to_array.
            y may be None if y_column is None.
            Defaults to None.
        shuffle : bool
            Whether to returned the rows in random order. Defaults to True.
        seed : int
            Seed to use for the random number generator.

        Returns
        -------
        :class:`brine.keras_generator.KerasGenerator`
            A generator that yields batches of samples (x, y) (or just x if y_column is None) from the dataset
            with processing_function applied.
            The generator will continue to yield samples indefinitely.
        """

        try:
            from brine.keras_generator import KerasGenerator
        except ImportError as e:
            if e.name != 'keras':
                raise
            else:
                print('Could not find keras. Please install keras before using this method')
                return None
        return KerasGenerator(self, x_column, y_column,
                              batch_size=batch_size, shuffle=shuffle, processing_function=processing_function,
                              seed=seed)

    def to_pytorch(self, transform=None, transform_columns=None):
        """Creates a PyTorch Dataset that can be passed to a PyTorch DataLoader.

        Parameters
        ----------
        transform : callable
            A callable to apply to each of the rows. If set to None, the default transform will be applied
            which converts any Image columns into PyTorch Tensors.
            Defaults to None.
        transform_columns : 'images' or None
            If transform_columns is set to 'images', each of the Image columns will be passed to the transform
            callable. This is useful to directly apply torchvision transforms on those columns.
            If transform_columns is set to None, the transform function will receive the namedtuple
            representing the entire Row from the Dataset.

        Returns
        -------
        PyTorch Dataset
        """
        try:
            from brine.pytorch_dataset import PytorchDataset
        except ImportError as e:
            if e.name != 'pytorch':
                raise
            else:
                print('Could not find pytorch. Please install pytorch before using this method')
                return None
        return PytorchDataset(self, transform=transform, transform_columns=transform_columns)

    def load_image(self, image_path, imread_fn=None):
        """Get the PIL image for an Image path in the dataset.

        Parameters
        ----------
        image_path : str
            The path to the image in the dataset. This should be retrieved directly from the Row
        imread_fn : callable
            The function to use to read the image. If None, the image will be read with `Image.open`.
            Defaults to None.

        Returns
        -------
        A PIL Image
        """

        p = os.path.join(self.dataset_manager.path, 'images', image_path)
        if imread_fn is None:
            return Image.open(p)
        else:
            return imread_fn(p)

    @property
    def columns(self):
        """Returns a list of Column objects containing information about each column in the dataset
        """
        return self.Column(*self.schema.columns)

    def __enter__(self):
        return self

    def __exit__(self, exc, value, tb):
        pass

    def __getitem__(self, index):
        """
        Returns
        -------
        Row namedtuple
            A namedtuple for the row at the given index.
        """
        if self.indices is None:
            real_index = index
        else:
            real_index = self.indices[index]
        row = list(self.metadata[real_index].item())
        for i, converter in self.converters.items():
            row[i] = converter(row[i])
        return self.Row(*row)

    def __len__(self):
        """
        Returns
        -------
        int
            The length of the entire dataset
        """
        if self.indices is None:
            return self.metadata.shape[0]
        else:
            return len(self.indices)

    def __iter__(self):
        return LoaderIter(self)


class LoaderIter(object):

    def __init__(self, loader):
        self.i = 0
        self.loader = loader

    def __iter__(self):
        return self

    def __next__(self):
        if self.i < len(self.loader):
            self.i = self.i + 1
            return self.loader[self.i - 1]
        else:
            raise StopIteration

    next = __next__


class DatasetError(BrineError):
    pass


class CategoryConverter(object):

    def __init__(self, categories):
        self.categories = categories

    def __call__(self, value):
        return self.categories[value]


class ArrayConverter(object):

    def __init__(self, items_converter):
        self.items_converter = items_converter

    def __call__(self, value):
        return [self.items_converter(x) for x in value]
