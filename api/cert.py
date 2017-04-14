#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
api.cert
'''

from utils.format import fmt, pfmt
from utils.isinstance import *

from utils.dictionary import head, body, head_body, keys_ending
from utils.exceptions import AutocertError

class VisitError(AutocertError):
    def __init__(self, obj):
        message = fmt('unknown type obj = {obj}')
        super(VisitError, self).__init__(message)

def create_cert_name(common_name, timestamp, sep='@'):
    return fmt('{common_name}{sep}{timestamp}')

def decompose_cert(cert):
    cert_name, cert_body = head_body(cert)
    common_name = cert_body['common_name']
    tardata_body = body(cert_body['tardata'])
    crt_filename = keys_ending(tardata_body, 'crt')[0]
    csr_filename = keys_ending(tardata_body, 'csr')[0]
    key_filename = keys_ending(tardata_body, 'key')[0]
    crt = tardata_body[crt_filename]
    csr = tardata_body[csr_filename]
    key = tardata_body[key_filename]
    return cert_name, common_name, crt, csr, key

def printit(obj):
    print(obj)
    return obj

def simple(obj):
    if istuple(obj):
        key, value = obj
        if isinstance(value, str) and key[-3:] in ('crt', 'csr', 'key'):
            value = key[-3:].upper()
        return key, value
    return obj

def abbrev(obj):
    if istuple(obj):
        key, value = obj
        if isinstance(value, str) and key[-3:] in ('crt', 'csr', 'key'):
            lines = value.split('\n')
            lines = lines[:2] + ['...'] + lines[-3:]
            from pprint import pprint
            pprint(dict(lines=lines))
            value = '\n'.join(lines)
        return key, value
    return obj

def visit(obj, func=printit):
    obj1 = None
    if isdict(obj):
        obj1 = {}
        for key, value in obj.items():
            if isscalar(value):
                key1, value1 = visit((key, value), func=func)
            else:
                key1 = key
                value1 = visit(value, func=func)
            obj1[key1] = value1
    elif islist(obj):
        obj1 = []
        for item in obj:
            obj1.append(visit(item, func=func))
    elif isscalar(obj) or istuple(obj) and len(obj) == 2:
        obj1 = func(obj)
    else:
        raise VisitError(obj)
    return obj1

