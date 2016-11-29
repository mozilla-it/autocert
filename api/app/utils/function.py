#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def format_docstr(func, *args, **kwargs):
    func.__doc__ = func.__doc__.format(*args, **kwargs)

