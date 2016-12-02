#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from copy import deepcopy
from glob import glob
from ruamel import yaml
from attrdict import AttrDict
from urlpath import URL
from pathlib2 import Path

class ConfigFileError(Exception):
    def __init__(pattern, errors=None):
        message = 'Could not find config file with pattern=%s'.format(pattern)
        super(ConfigFileError, self).__init__(message)
        self.errors = errors

class ConfigLoadError(Exception):
    def __init__(config, errors=None):
        message = 'Error loading config file =%s'.format(config)
        super(ConfigLoadError, self).__init__(message)
        self.errors = errors

class AuthKeyNotAllowedError(Exception):
    def __init__(d, errors=None):
        message = '"auth" key found on dict =%s'.format(d)
        super(AuthKeyNotAllowedError, self).__init__(message)
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

def _fixup(obj):
    if isinstance(obj, dict):
        d = deepcopy(obj)
        for k,v in obj.items():
            if isinstance(v, str):
                if 'url' in k:
                    d[k] = URL(v)
                elif 'path' in k:
                    d[k] = Path(v)
                elif 'apikey' in k:
                    if 'auth' in d or 'auth' in obj:
                        raise AuthKeyNotAllowedError(d)
                    d['auth'] = (k, v)
            elif isinstance(v, dict):
                d[k] = _fixup(v)
        return d
    return obj

def _load_config():
    config = _divine_config()
    try:
        obj = yaml.safe_load(open(config))
        obj = _fixup(obj)
    except Exception as ex:
        print('ex =', ex)
        raise ConfigLoadError(config, errors=[ex])
    return AttrDict(obj)

CFG = _load_config()
