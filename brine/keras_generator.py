import numpy as np
import threading
from keras.preprocessing.image import img_to_array
from brine.iterator import Iterator


class KerasGenerator(object):
    """A generator that yields batches of samples. Can be used with Keras' `fit_generator` and `predict_generator`.

    Refer to documentation for :meth:`brine.dataset.Dataset.to_keras`.
    """
    def __init__(self, dataset, x_column, y_column=None, batch_size=32,
                 shuffle=True, seed=None, processing_function=None):
        self.dataset = dataset
        self.x_column = getattr(dataset.columns, x_column)
        if y_column is not None:
            self.y_column = getattr(dataset.columns, y_column)
        else:
            self.y_column = None
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.processing_function = processing_function
        self.lock = threading.Lock()
        self.index_generator = Iterator().flow_index(len(self.dataset),
                                                     batch_size=batch_size, shuffle=shuffle, seed=seed)

    def __iter__(self):
        return self

    def next(self):
        with self.lock:
            index_array, current_index, current_batch_size = next(self.index_generator)
        xs = []
        ys = []
        for i, index in enumerate(index_array):
            row = self.dataset[index]
            x = getattr(row, self.x_column.name)
            x = self._preprocess_field(self.x_column, x)

            if self.y_column is not None:
                y = getattr(row, self.y_column.name)
                y = self._preprocess_field(self.y_column, y)
            else:
                y = None

            if self.processing_function is not None:
                data = self.processing_function((x, y))

            x = data[0]
            xs.append(x)
            if self.y_column is not None:
                y = data[1]
                ys.append(y)

        if self.y_column is not None:
            return np.stack(xs), np.stack(ys)
        else:
            return np.stack(xs)

    def steps_per_epoch(self):
        """The number of batches in one full epoch.

        Equal to the number of rows in the dataset divided by the batch size.

        Returns
        -------
        int
        """
        dataset_len = len(self.dataset)
        if dataset_len % self.batch_size == 0:
            return int(dataset_len/self.batch_size)
        else:
            return (int(dataset_len/self.batch_size) + 1)

    def __next__(self, *args, **kwargs):
        return self.next(*args, **kwargs)

    def _preprocess_field(self, column, value):
        if column.isimage():
            value = img_to_array(self.dataset.load_image(value))
        elif column.categories is not None:
            value = self._get_category_index(column, value)
        return value

    def _get_category_index(self, column, value):
        # TODO(rohan): Use a dict for this
        if isinstance(value, tuple):
            return tuple(map(lambda v: column.categories.index(v), value))
        else:
            return column.categories.index(value)
