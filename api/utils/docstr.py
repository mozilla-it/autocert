#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import inspect

def docstr():
    frame = inspect.currentframe().f_back
    funcname = frame.f_code.co_name
    globals_ = frame.f_globals
    func = globals_[funcname]
    return func.__doc__
