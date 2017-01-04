#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.transform
'''
import requests
from attrdict import AttrDict

from cli.utils.dictionary import head, body

def summarize(certs):
    return [{head(cert): body(cert)['expires']} for cert in certs]

def detail(certs):
    results = []
    for cert in certs:
        name = head(cert)
        data = body(cert)
        data.get('authorities', {}).get('digicert', {}).pop('data', None)
        results += [{name: data}]
    return results

def transform(results, verbosity):
    if verbosity == 1:
        return detail(results)
    elif verbosity == 2:
        return results
    return summarize(results)

