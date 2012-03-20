#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='django-orm-extender',
    version='0.1',
    author='Michael Bashkirov',
    author_email='bashmish@gmail.com',
    url='https://github.com/bashmish/django-orm-extender',
    description='Useful features missing from Django ORM.',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Database',
        'Topic :: Software Development'
    ],
)
