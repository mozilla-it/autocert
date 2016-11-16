#!/usr/bin/env python3

import os

def dirname(path, count=1):
    for x in range(count):
        path = os.path.dirname(path)
    return path

def describe():
    from subprocess import check_output
    return check_output('git describe', shell=True).decode('utf-8').strip()

def version():
    versionfile = dirname(__file__, 3) + '/VERSION'
    version = open(versionfile).read() if os.path.exists(versionfile) else describe()
    version, *suffix = version.split('-')
    if suffix:
        version = version.replace('v', '') + '.dev{0}+{1}'.format(*suffix)
    return version
