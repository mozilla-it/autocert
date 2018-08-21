#!/usr/bin/env python3

import sys
from pprint import pprint

def pytest_configure(config):
    # added rootdir to sys.path so that imports would work in tests/*
    print('config.rootdir:', config.rootdir)
    path = '/'.join([str(config.rootdir), 'autocert/'])
    sys.path.insert(0, path)
