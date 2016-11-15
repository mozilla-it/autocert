#!/usr/bin/env python3

import inspect

from pprint import pprint

import json

def jsonify(string):
    return json.loads(str(string))

def docstr():
    frame = inspect.currentframe().f_back
    funcname = frame.f_code.co_name
    globals_ = frame.f_globals
    func = globals_[funcname]
    return func.__doc__
