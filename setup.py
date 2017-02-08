#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''setup.py: setuptools control.'''

from setuptools import setup
import re

def version():
    from subprocess import check_output
    version = check_output('git describe', shell=True).decode('utf-8').strip()
    version, *suffix = version.split('-')
    if suffix:
        version = version.replace('v', '') + '.dev{0}+{1}'.format(*suffix)
    return version

__version__ = version()

setup(
    name = 'autocert-cli',
    packages = ['cli'],
    entry_points = {
        'console_scripts': ['autocert = cli.cli:main']
    },
    version = __version__,
    description = 'autocert cli tool',
    long_description = open('README.md').read().strip(),
    license = open('LICENSE').read().strip(),
    install_requires=open('requirements.txt').readlines(),
    author = 'Scott Idler',
    author_email = 'scott.a.idler@gmail.com',
    url = 'https://github.com/mozilla-it/autocert',
)
