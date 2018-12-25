#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.requests: wrapper around requests specific to cli
'''
import requests
import getpass
import platform

from requests import Session, Request

from urllib.parse import urlparse

USER = getpass.getuser()
HOSTNAME = platform.node()

def request(method, url, json=None, **kwargs):
    hostname = urlparse(str(url)).hostname
    verify = hostname not in ('0.0.0.0', 'localhost')
    json = json if json else {}
    json['user'] = USER
    json['hostname'] = HOSTNAME
    if not verify:
        requests.packages.urllib3.disable_warnings()
    return requests.request(method, url, json=json, verify=verify, **kwargs)

def get(url, **kwargs):
    return request('GET', url, **kwargs)

def put(url, **kwargs):
    return request('PUT', url, **kwargs)

def post(url, **kwargs):
    return request('POST', url, **kwargs)

def delete(url, **kwargs):
    return request('DELETE', url, **kwargs)
