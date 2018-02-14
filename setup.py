# coding=utf-8
"""
Setup for ImageSplit

Author: Tom Doel
Copyright UCL 2017

"""

from setuptools import setup, find_packages
import os

from imagesplit.utils.versioning import version_from_git


version_git = version_from_git('0.0.0')

# Create a module that will keep the
# version descriptor returned by Git
info_module = open(os.path.join('imagesplit', 'info.py'), 'w')
info_module.write('# -*- coding: utf-8 -*-\n')
info_module.write('"""ImageSplit version tracker.\n')
info_module.write('\n')
info_module.write('This module only holds the ImageSplit version')
info_module.write('\n')
info_module.write('"""\n')
info_module.write('\n')
info_module.write('\n')
info_module.write('VERSION_DESCRIPTOR = "{}"\n'.format(version_git))
info_module.close()

# Get the summary
description = 'Utility for splitting large image files into slices or chunks'\

# Get the long description
with open('README.rst') as f:
    long_description = f.read()


setup(
    name='ImageSplit',

    version=version_git,

    description=description,
    long_description=long_description,

    url='https://github.com/gift-surg/ImageSplit',

    author='Tom Doel',
    author_email='t.doel@ucl.ac.uk',

    license='BSD license',

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Intended Audience :: Healthcare Industry',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',

        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',

        'Topic :: Scientific/Engineering :: Image Recognition',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Medical Science Apps.',
        'Topic :: Scientific/Engineering :: Visualization',
    ],

    keywords='image file formats',

    packages=find_packages(
        exclude=[
            'pip',
            'docs',
            'tests',
        ]
    ),

    install_requires=[
        'six>=1.10',
        'numpy>=1.11',
        'pillow',
    ],

    entry_points={
        'console_scripts': [
            'imagesplit=imagesplit.applications.split_files:main',
        ],
    },
)
