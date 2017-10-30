===============
Getting Started
===============

The following is a quick start guide to using Brine. We'll be using the CIFAR10
dataset with a simple PyTorch classifier.

Installation
------------

Brine is a pip package, so we can install it with::

  $ pip install brine-io

At this time, Brine is only compatible with Python 3, but Python 2 support is
coming soon.

Download a Dataset
------------------

To download the CIFAR10 dataset, we'll use the brine CLI. In your project
directory, run::

  $ brine install cifar10/train

Loading a Dataset
-----------------

To load this dataset, we'll be using the :func:`~brine.dataset.load_dataset` function::

  >> import brine
  >> cifar_train = brine.load_dataset('cifar10/train')

By using the :attr:`~brine.dataset.Dataset.columns` property of the Dataset we
can take a look at the structure of this dataset::

  >> cifar_train.columns
  Column(image=Column(name=image, type=Image), label=Column(name=label, type=Category, categories=['dog', 'horse', 'frog', 'airplane', 'cat', 'ship', ...]))

Columns returns a named tuple indexed by the column name.
Since `label` is a category column, we can also see the categories that column
contains. We'll save these in a local variable for later::

  >> categories = cifar_train.columns.label.categories
  >> categories
  ['dog', 'horse', 'frog', 'airplane', 'cat', 'ship', 'deer', 'bird', 'truck', 'automobile']

We can check the length of the dataset by using `len`::

  >> len(cifar_train)
  50000

To access any row from the dataset, we simply need to index into it. This
returns a named tuple that we can use to access the individual fields::

  >> cifar_train[20]
  Row(image='46405_bird.png', label='bird')
  >> cifar_train[20].image
  '46405_bird.png'
  >> cifar_trian[20].label
  'bird'

The `image` field returns an Image Path. To load the image, we use the Dataset's
:meth:`~brine.dataset.Dataset.load_image` method::

  >> cifar_train.load_image(cifar_train[20].image)
  <PIL.PngImagePlugin.PngImageFile image mode=RGB size=32x32 at 0x7F9BA7860D68>

We can also split our dataset into multiple folds using
:meth:`~brine.dataset.Dataset.create_folds`. This is useful for creating
train/validation splits. Each fold is a brine Dataset (no additional disk
space is used) so you can perform all the same actions on a fold as on the original
Dataset. Let's set aside 2000 samples for our validation fold. The rest of the
samples will go in our training fold::

  >> validation_fold, training_fold = cifar_train.create_folds([2000],
  shuffle=True)
  >> len(validation_fold)
  2000
  >> len(training_fold)
  48000

Interfacing with PyTorch
------------------------

Brine provides methods to convert your Brine dataset into a format compatible
with popular ML frameworks like PyTorch and Keras.

Here's an example using PyTorch::

  from torchvision import transforms
  transform = transforms.Compose(
      [transforms.ToTensor(),
      transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])

  train_fold_pytorch = training_fold.to_pytorch(transform=transform, transform_columns='images')
  validation_fold_pytorch = validation_fold.to_pytorch(transform=transform, transform_columns='images')

The :meth:`~brine.dataset.Dataset.to_pytorch` method returns a PyTorch Dataset. 
The `transform` callable is applied to each row in the dataset. Since we
specified `transform_columns='images'`, the transform will only be applied to
the Image columns (in this case 'image'). The Image columns will be converted to
PIL images before being passed to the transform.

We can use this PyTorch Dataset just as we'd use any other PyTorch Dataset. For
example, we use it to create a DataLoader::

  trainloader = torch.utils.data.DataLoader(train_fold_pytorch, batch_size=4, shuffle=True, num_workers=2)

Conclusion
----------

That's it! These same methods can be applied to any dataset installed via Brine,
including datasets for segmentation, simple classification, multi-class
classification and object detection.

For an example of using Brine to do image segmentation with Keras, check out
`this blog post <https://medium.com/@hanrelan/a-non-experts-guide-to-image-segmentation-using-deep-neural-nets-dda5022f6282>`_.
