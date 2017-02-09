#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utils.format import fmt, pfmt
from utils.isinstance import *

def create_cert_name(common_name, timestamp, sep='@'):
    return fmt('{common_name}{sep}{timestamp}')

def decompose_cert_name(cert_name, sep='@'):
    return cert_name.split(sep)

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

def visit(obj, func=printit):
    obj1 = None
    if isdict(obj):
        obj1 = {}
        for key, value in obj.items():
            obj1[key] = visit(value, func=func)
    elif isiter(obj):
        obj1 = []
        for item in obj:
            obj1.append(visit(item, func=func))
    elif isscalar(obj):
        obj1 = func(obj)
    return obj1
