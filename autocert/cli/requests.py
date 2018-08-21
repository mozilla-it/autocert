#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.requests: wrapper around requests specific to cli
'''
import requests
import getpass
import platform

USER = getpass.getuser()
HOSTNAME = platform.node()

def request(method, url, json=None, **kwargs):
    json = json if json else {}
    json['user'] = USER
    json['hostname'] = HOSTNAME
    return requests.request(method, url, json=json, **kwargs)

def get(url, **kwargs):
    return request('GET', url, **kwargs)

def put(url, **kwargs):
    return request('PUT', url, **kwargs)

def post(url, **kwargs):
    return request('POST', url, **kwargs)

def delete(url, **kwargs):
    return request('DELETE', url, **kwargs)
