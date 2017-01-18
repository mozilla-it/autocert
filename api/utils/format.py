#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
format: here there be baby dragons!
'''

import inspect
from pprint import pprint, pformat

from utils.dictionary import merge

def fmt_dict(obj):
    if isinstance(obj, dict):
        return pformat(obj)
    return str(obj)

def _fmt(string, args, kwargs, do_print=False):
    '''
    here there be baby dragons!
    '''
    try:
        if args or kwargs:
            return string.format(
                *[fmt_dict(arg) for arg in args],
                **{k:fmt_dict(v) for k,v in kwargs.items()})
        frame = inspect.currentframe().f_back.f_back
        gl = dict(locals=frame.f_locals, globals=frame.f_globals)
        gl.update(frame.f_globals)
        gl.update(frame.f_locals)
        if frame.f_code.co_name == '<listcomp>':
            frame = frame.f_back
            gl.update(frame.f_locals)
        s = string.format(**{k:fmt_dict(v) for k,v in gl.items()})
    except KeyError as ke:
        print('keyerror not found in following keys of gl dict:')
        pprint(list(gl.keys()))
        raise ke
    if do_print:
        print(s)
    return s

def fmt(string, *args, **kwargs):
    return _fmt(string, args, kwargs)

def pfmt(string, *args, **kwargs):
    return _fmt(string, args, kwargs, do_print=True)
