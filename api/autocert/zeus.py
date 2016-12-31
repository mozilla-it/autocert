#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
module specific to talking with zeus load balancer
'''

import requests
from attrdict import AttrDict
from pprint import pprint, pformat
from fnmatch import fnmatch

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from autocert.utils.dictionary import merge

try:
    from autocert.app import app
except ImportError:
    from app import app

try:
    from autocert.config import CFG
except ImportError:
    from config import CFG

def request(method, zeusdest, path, json=None):
    authority = AttrDict(CFG.destinations.zeus[zeusdest])
    url = authority.baseurl / path
    response = requests.request(method, url, verify=False, auth=authority.auth, headers=authority.headers, json=json)
    try:
        obj = AttrDict(response.json())
    except ValueError:
        obj = None
    return response, obj

def get(zeusdest, path):
    return request('GET', zeusdest, path)

def put(zeusdest, path, json=None):
    return request('PUT', zeusdest, path, json=json)

def post(zeusdest, path, json=None):
    return request('POST', zeusdest, path, json=json)

def get_installed_certificates(zeusdest, pattern='*'):
    r, o = get(zeusdest, 'ssl/server_keys')
    certs = {}
    if r.status_code == 200:
        for record in o.children:
            name = record['name']
            if fnmatch(name, pattern):
                r, o = get(zeusdest, 'ssl/server_keys/' + name)
                if r.status_code == 200:
                    certs.update({name : dict(o.properties.basic)})
                else:
                    print(r.status_code, r.text)
    else:
        print(r.status_code, r.text)
    return {zeusdest: certs}
