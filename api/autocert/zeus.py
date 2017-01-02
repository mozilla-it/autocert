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

class GetInstalledCertificatesSummaryError(Exception):
    def __init__(self, response):
        msg = 'error during get installed certificates summary: {0}'.format(response)
        super(GetInstalledCertificatesSummaryError, self).__init__(msg)

class GetInstalledCertificatesDetailsError(Exception):
    def __init__(self, response):
        msg = 'error during get installed certificates details: {0}'.format(response)
        super(GetInstalledCertificatesDetailsError, self).__init__(msg)

def request(method, zeusdest, path, json=None, attrdict=True):
    authority = AttrDict(CFG.destinations.zeus[zeusdest])
    url = authority.baseurl / path
    response = requests.request(method, url, verify=False, auth=authority.auth, headers=authority.headers, json=json)
    try:
        obj = response.json()
        if attrdict:
            obj = AttrDict(obj)
    except ValueError:
        obj = None
    return response, obj

def get(zeusdest, path, attrdict=True):
    return request('GET', zeusdest, path, attrdict=attrdict)

def put(zeusdest, path, json=None, attrdict=True):
    return request('PUT', zeusdest, path, json=json, attrdict=attrdict)

def post(zeusdest, path, json=None, attrdict=True):
    return request('POST', zeusdest, path, json=json, attrdict=attrdict)

def get_installed_certificates_summary(zeusdest, common_name_pattern='*'):
    r, o = get(zeusdest, 'ssl/server_keys')
    if r.status_code == 200:
        summary = {}
        for child in o.children:
            if fnmatch(child.name, common_name_pattern):
                summary[child.name] = child.href
        return summary
    raise GetInstalledCertificatesSummaryError(r)

def get_installed_certificates_details(zeusdest, summary):
    details = {}
    for common_name, href in summary.items():
        r, o = get(zeusdest, 'ssl/server_keys/' + common_name)
        if r.status_code == 200:
            details[common_name] = {
                'destinations': [{
                    zeusdest: dict(o.properties.basic)
                }]
            }
            continue
        raise GetInstalledCertificatesDetailsError(r)
    return details

def get_installed_certificates(zeusdest_pattern='*', common_name_pattern='*'):
    zeusdests = CFG.destinations.zeus.keys()
    zeusdests = [zeusdest for zeusdest in zeusdests if fnmatch(zeusdest, zeusdest_pattern)]
    installed = {}
    for zeusdest in zeusdests:
        summary = get_installed_certificates_summary(zeusdest, common_name_pattern)
        details = get_installed_certificates_details(zeusdest, summary)
        installed = merge(installed, details)
    return installed
