from setuptools import setup, find_packages


setup(
    name='brine-io',
    description='Dataset management for computer vision',
    long_description='Dataset management for computer vision',
    version='0.5.0',
    url='https://github.com/brine-io/brine',
    download_url='https://github.com/brine-io/brine/archive/0.5.0.tar.gz',
    author='David Ye',
    author_email='david@brine.io',
    keywords='brine',
    license='LICENSE',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    packages=find_packages(),
    install_requires=[
        "requests>=2.14.0",
        "tqdm>=4.17.0",
        "numpy>=1.7.0",
        "bcolz>=1.1.1",
        "pandas>=0.19.0",
        "pillow",
    ],
    entry_points={
        'console_scripts': [
            'brine=brine.__main__:main',
        ],
    },
    python_requires='>=3',
)
