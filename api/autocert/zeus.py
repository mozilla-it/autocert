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
from autocert.utils.newline import windows2unix

try:
    from autocert.app import app
except ImportError:
    from app import app

try:
    from autocert.config import CFG
except ImportError:
    from config import CFG

class ZeusRequiresHttpsForPutsError(Exception):
    def __init__(self, url):
        msg = 'zeus requires https protocol; url = {0}'.format(url)
        super(ZeusRequiresHttpsForPutsError, self).__init__(msg)

class GetInstalledCertificatesSummaryError(Exception):
    def __init__(self, response):
        msg = 'error during get installed certificates summary: {0}'.format(response)
        super(GetInstalledCertificatesSummaryError, self).__init__(msg)

class GetInstalledCertificatesDetailsError(Exception):
    def __init__(self, response):
        msg = 'error during get installed certificates details: {0}'.format(response)
        super(GetInstalledCertificatesDetailsError, self).__init__(msg)

class ZeusCertificateInstallError(Exception):
    def __init__(self, response):
        msg = 'error during install of certificate: {0}'.format(response)
        super(ZeusCertificateInstallError, self).__init__(msg)

def request(method, zeusdest, path, json=None, attrdict=True):
    authority = AttrDict(CFG.destinations.zeus[zeusdest])
    url = authority.baseurl / path
    if not str(url).startswith('https'):
        raise ZeusRequiresHttpsForPutsError(url)
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

def put_certificate(common_name, key, csr, crt, *zeusdests):
    print('common_name =', common_name)
    for zeusdest in zeusdests:
        print('zeusdest =', zeusdest)
        json = {
            'properties': {
                'public': {
                    'note': 'auto-cert deploy',
                    'private': key,
                    'request': csr,
                    'public': crt,
                }
            }
        }
        print('json =', json)
        r, o = put(zeusdest, 'ssl/server_keys/' + common_name, json=json)
        if r.status_code != 201:
            print(r.status_code)
            print(r.text)
            raise ZeusCertificateInstallError(r)

def get_installed_certificates_summary(zeusdest, common_name='*'):
    r, o = get(zeusdest, 'ssl/server_keys')
    if r.status_code == 200:
        summary = {}
        for child in o.children:
            if fnmatch(child.name, common_name):
                summary[child.name] = child.href
        return summary
    raise GetInstalledCertificatesSummaryError(r)

def get_installed_certificates_details(zeusdest, csr, summary):
    details = {}
    for common_name, href in summary.items():
        r, o = get(zeusdest, 'ssl/server_keys/' + common_name)
        if r.status_code == 200:
            if o.properties.basic.request == csr:
                details[common_name] = {
                    'destinations': [{
                        zeusdest: {
                            'note': o.properties.basic.note,
                            'key': windows2unix(o.properties.basic.private),
                            'csr': windows2unix(o.properties.basic.request),
                            'crt': windows2unix(o.properties.basic.public),
                        }
                    }]
                }
            continue
        raise GetInstalledCertificatesDetailsError(r)
    return details

def get_installed_certificates(csr, common_name='*', *zeusdests):
    installed = {}
    for zeusdest in zeusdests:
        summary = get_installed_certificates_summary(zeusdest, common_name)
        details = get_installed_certificates_details(zeusdest, csr, summary)
        installed = merge(installed, details)
    return installed
