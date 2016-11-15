#!/usr/bin/env python3

import sys
from pprint import pprint

def pytest_configure(config):
    # added rootdir to sys.path so that imports would work in tests/*
    path = '/'.join([str(config.rootdir), 'api'])
    sys.path.insert(0, path)
