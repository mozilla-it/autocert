#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
format: here there be baby dragons!
'''

import re
import ast
import inspect
from pprint import pprint, pformat

__all__ = [
    'dbg',
    'fmt',
    'pfmt',
]

class FmtKeyError(Exception):
    def __init__(self, keys):
        msg = 'fmt error; key not found in keys: ' + ' '.join(keys)
        super(FmtKeyError, self).__init__(msg)

def dbg(*args, logger=None, **kwargs):
    frame = inspect.currentframe().f_back
    return _dbg(args, kwargs, frame, logger=logger)

def fmt(string, *args, **kwargs):
    frame = inspect.currentframe().f_back
    return _fmt(string, args, kwargs, frame)

def pfmt(string, *args, **kwargs):
    frame = inspect.currentframe().f_back
    return _fmt(string, args, kwargs, frame, do_print=True)

def _create_format(name):
    try:
        return str(ast.literal_eval(name))
    except:
        pass
    return name+'="{'+name+'}"'

_dbg_regex = re.compile(r'p?dbg\s*\((.+?)\)$')

def _dbg(args, kwargs, frame, logger=None):
    klass = frame.f_locals.get('self', None)
    string = 'DBG: '
    if klass:
        string += klass.__class__.__name__ + '.'
    string += frame.f_code.co_name + ': '
    if args or kwargs:
        context = inspect.getframeinfo(frame).code_context
        callsite = ''.join([line.strip() for line in context])
        match = _dbg_regex.search(callsite)
        if match:
            params = [param.strip() for param in match.group(1).split(',')]
        names = params[:len(args)] + list(kwargs.keys())
        string += ' '.join([_create_format(name) for name in names])
    else:
        string += 'locals:\n{locals}'
    result = _fmt(string, args, kwargs, frame, do_print=logger is None)
    if logger:
        logger.debug(result)
    return result

def _fmt_dict(obj):
    if isinstance(obj, dict):
        return pformat(obj)
    return str(obj)

def _fmt(string, args, kwargs, frame, do_print=False):
    try:
        gl = {
            'locals': frame.f_locals,
            'globals': frame.f_globals,
        }
        gl.update(frame.f_globals)
        gl.update(frame.f_locals)
        gl.update(kwargs)
        if frame.f_code.co_name == '<listcomp>':
            gl.update(frame.f_back.f_locals)
        result= string.format(*args, **{k:_fmt_dict(v) for k,v in gl.items()})
    except KeyError as ke:
        raise FmtKeyError(gl)
    if do_print:
        print(result)
    return result
