#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
module specific to talking with zeus load balancer
'''

import requests
from attrdict import AttrDict
from pprint import pformat

from autocert.utils.dictionary import merge

try:
    from autocert.app import app
except ImportError:
    from app import app

try:
    from autocert.config import CFG
except ImportError:
    from config import CFG

def request(method, path, json=None):
    authority = CFG.destinations.zeus
    url = authority.baseurl / path
    response = requests.request(method, url, auth=authority.auth, json=json)
    try:
        ad = AttrDict(response.json())
    except ValueError:
        ad = None
    return response, ad

def get(path):
    return request('GET', path)

def put(path, json=None):
    return request('PUT', path, json=json)

def post(path, json=None):
    return request('POST', path, json=json)
