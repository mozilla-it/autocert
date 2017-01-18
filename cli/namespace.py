#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.namespace: to jsonify namespace with user and hostname
'''

import platform
import getpass
import copy

def jsonify(ns, **kwargs):
    json = copy.deepcopy(ns.__dict__)
    json.pop('func')
    for k,v in kwargs.items():
        json[k] = v
    json['user'] = getpass.getuser()
    json['hostname'] = platform.node()
    json['api_url'] = str(json['api_url']) #FIXME: ugly wart to remove
    return json

