#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def dict_to_attrs(obj, d):
    for k, v in d.items():
        setattr(obj, k, v)
    return obj

def update(d1, d2):
    d1.update(d2)
    return d1

def isstr(obj):
    return isinstance(obj, str)

def isint(obj):
    return isinstance(obj, int)

def isfloat(obj):
    return isinstance(obj, float)

def isscalar(obj):
    return (obj == None) or isstr(obj) or isint(obj) or isfloat(obj)

class MergeError(Exception):
    def __init__(self, msg):
        self.msg = msg

def merge(obj1, obj2):
    """merges obj2 into obj1 and return merged result

    NOTE: tuples and arbitrary objects are not handled as it is totally ambiguous what should happen"""
    key = None
    try:
        if isscalar(obj1):
            obj1 = obj2
        elif isinstance(obj1, list):
            if isinstance(obj2, list):
                obj1.extend(obj2)
            else:
                obj1.append(obj2)
        elif isinstance(obj1, dict):
            if isinstance(obj2, dict):
                for key in obj2:
                    if key in obj1:
                        obj1[key] = merge(obj1[key], obj2[key])
                    else:
                        obj1[key] = obj2[key]
            else:
                raise MergeError('Cannot merge non-dict "%s" into dict "%s"' % (obj2, obj1))
        else:
            raise MergeError('NOT IMPLEMENTED "%s" into "%s"' % (obj2, obj1))
    except TypeError as e:
        raise MergeError('TypeError "%s" in key "%s" when merging "%s" inExceptio://www.youtube.com/watch?v=A_AkDugh7IAto "%s"' % (e, key, obj2, obj1))
    return obj1
