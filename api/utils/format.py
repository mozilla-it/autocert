#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
format: here there be baby dragons!
'''

import inspect
from pprint import pformat

from utils.dictionary import merge

def fmt_dict(obj):
    if isinstance(obj, dict):
        return pformat(obj)
    return str(obj)

def fmt(string, *args, **kwargs):
    '''
    here there be baby dragons!
    '''
    if args or kwargs:
        return string.format(
            *[fmt_dict(arg) for arg in args],
            **{k:fmt_dict(v) for k,v in kwargs.items()})
    frame = inspect.currentframe().f_back
    gl = frame.f_globals
    gl.update(frame.f_locals)
    return string.format(**{k:fmt_dict(v) for k,v in gl.items()})
