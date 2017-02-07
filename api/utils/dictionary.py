#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from copy import deepcopy

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

def _merge(obj1, obj2):
    """merges obj2 into obj1 and return merged result

    NOTE: tuples and arbitrary objects are not handled as it is totally ambiguous what should happen"""
    key = None
    result = deepcopy(obj1)
    try:
        if isscalar(result):
            result = obj2
        elif isinstance(result, list):
            if isinstance(obj2, list):
                result.extend(obj2)
            else:
                result.append(obj2)
        elif isinstance(result, dict):
            if isinstance(obj2, dict):
                for key in obj2:
                    if key in result:
                        result[key] = _merge(result[key], obj2[key])
                    else:
                        result[key] = obj2[key]
            else:
                raise MergeError('Cannot merge non-dict "%s" into dict "%s"' % (obj2, result))
        else:
            raise MergeError('NOT IMPLEMENTED "%s" into "%s"' % (obj2, result))
    except TypeError as e:
        raise MergeError('TypeError "%s" in key "%s" when merging "%s" inExceptio://www.youtube.com/watch?v=A_AkDugh7IAto "%s"' % (e, key, obj2, result))
    return result

def merge(*objs):
    if len(objs) == 0:
        return {}
    elif len(objs) == 1:
        return objs[0]
    result = objs[0]
    for obj in objs[1:]:
        result = _merge(result, obj)
    return result

class DictDoesntHaveHeadError(Exception):
    def __init__(self, d):
        keys = list(d.keys())
        msg = 'dictionary.keys(): {keys} does not have a single key to be considered a head'.format(**locals())
        super(DictDoesntHaveHeadError, self).__init__(msg)

def head(d):
    assert isinstance(d, dict)
    keys = list(d.keys())
    if len(keys) == 1:
        return keys[0]
    raise DictDoesntHaveHeadError(d)

def body(d):
    return d[head(d)]

def head_body(d):
    head_ = head(d)
    return head_, d[head_]

def keys_ending(d, suffix):
    return [k for k in d.keys() if k.endswith(suffix)]

def dictify(items, sep=':'):
    result = {}
    if items:
        for item in items:
            key, value = item.split(sep)
            result[key] = result.get(key, []) + [value]
    return result

