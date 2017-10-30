from torch.utils.data import Dataset


class ImagePathToImage(object):
    """Transform that converts an Image Path into a PIL image.
    """
    def __init__(self, dataset, filepaths):
        self.dataset = dataset
        self.filepaths = filepaths

    def __call__(self, row):
        images = {filepath: self.dataset.load_image(getattr(row, filepath)) for filepath in self.filepaths}
        return row._replace(**images)


class PytorchDataset(Dataset):
    """A PyTorch Dataset that returns rows from the Brine Dataset. Can be used anywhere a PyTorch Dataset is used,
    including with PyTorch DataLoaders.

    See documentation for :meth:`~brine.dataset.Dataset.to_pytorch`
    """
    def __init__(self, dataset, transform=None, transform_columns=None):
        self.dataset = dataset
        self.image_columns = {column.name for column in self.dataset.columns if column.isimage()}
        self.category_columns = {column for column in self.dataset.columns if column.categories is not None}
        if (transform_columns is not None) and (transform is None):
            raise "transform must be set if transform_columns is set"
        if transform is not None:
            self.transform = transform
            self.transform_columns = transform_columns
        else:
            self.transform = ImagePathToImage(dataset, self.image_columns)
            self.transform_columns = None

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, index):
        row = self.dataset[index]
        category_indexed = {column.name: self._get_category_index(column, getattr(row, column.name))
                            for column in self.category_columns}
        row = row._replace(**category_indexed)
        if self.transform_columns == 'images':
            for column_name in self.image_columns:
                image = self.dataset.load_image(getattr(row, column_name))
                row = row._replace(**{column_name: self.transform(image)})
        else:
            row = self.transform(row)
        return row

    def _get_category_index(self, column, value):
        # TODO(rohan): Use a dict for this
        if isinstance(value, tuple):
            return tuple(map(lambda v: column.categories.index(v), value))
        else:
            return column.categories.index(value)
