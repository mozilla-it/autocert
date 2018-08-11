#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import glob
import fnmatch

from utils.fmt import fmt, pfmt

def regexes(items, includes=None, excludes=None):
    return _sift(items, includes, excludes, _include_regex, _exclude_regex)

def fnmatches(items, includes=None, excludes=None):
    if '*' in includes and not excludes:
        return items
    return _sift(items, includes, excludes, _include_fnmatch, _exclude_fnmatch)

def globs(dirpath, includes=None, excludes=None):
    items = os.path.listdir(dirpath)
    return fnmatches(items, includes, excludes, _include_fnmatch, _exclude_fnmatch)

def _sift(items, includes, excludes, include_fn, exclude_fn):
    items = [item for item in items if include_fn(item, includes)]
    items = [item for item in items if exclude_fn(item, excludes)]
    return items

def _include_fnmatch(item, includes):
    if not includes: includes = ['*']
    return any([fnmatch.fnmatch(item, include) for include in includes])

def _exclude_fnmatch(item, excludes):
    if not excludes: excludes = ['']
    return all([not fnmatch.fnmatch(item, exclude) for exclude in excludes])

def _include_regex(item, includes):
    if not includes: includes = ['.*']
    raise NotImplementedError

def _exclude_regex(item, excludes):
    if not excludes: excludes = ['()']
    raise NotImplementedError
