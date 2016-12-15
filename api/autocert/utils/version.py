#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from subprocess import check_output

def dirname(path, count=1):
    for x in range(count):
        path = os.path.dirname(path)
    return path

def describe():
    from subprocess import check_output
    return check_output('git describe', shell=True).decode('utf-8').strip()


_version = None
def version():
    global _version
    versionfile = dirname(__file__, 3) + '/VERSION'
    if not _version:
        _version = open(versionfile).read() if os.path.exists(versionfile) else describe()
        _version, *suffix = _version.split('-')
        if suffix:
            _version = _version.replace('v', '') + '.dev{0}+{1}'.format(*suffix)
    return _version
