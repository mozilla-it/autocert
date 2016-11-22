#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from glob import glob
from ruamel import yaml
from attrdict import AttrDict

class ConfigFileError(Exception):
    def __init__(pattern, errors=None):
        message = 'Could not find config file with pattern=%s'.format(pattern)
        super(ConfigFileError, self).__init__(message)
        self.errors = errors

class ApikeyNotFoundError(Exception):
    def __init__(d, errors=None):
        message = 'Could not find apikey in this dict %s' % d
        super(ApikeyNotFoundError, self).__init__(message)
        self.errors = errors

def _divine_config(pattern='config.yml*'):
    dirpath = os.path.dirname(__file__)
    matches = glob('/'.join([dirpath, pattern]))
    if matches:
        return sorted(matches)[0]
    raise ConfigFileError(pattern)

def _load_config():
    config = _divine_config()
    try:
        yml = yaml.load(open(config))
    except Exception as ex:
        raise ConfigLoadError(config, errors=[ex])
    return AttrDict(yml)


def auth(d):
    if 'apikey' in d:
        return ('apikey', d['apikey'])
    raise ApikeyNotFoundError(d)

CFG = _load_config()
