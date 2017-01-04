#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
autocert.update
'''

from pprint import pformat
from attrdict import AttrDict
from flask import make_response, jsonify, request

from autocert import digicert

try:
    from autocert.app import app
except ImportError:
    from app import app

try:
    from autocert.config import CFG
except ImportError:
    from config import CFG

class MissingUpdateArgumentsError(Exception):
    def __init__(self, args):
        msg = 'missing arguments to update; args = {0}'.format(args)
        super(MissingUpdateArgumentsError, self).__init__(msg)

def defaults(json):
    if not json:
        json = {}
    json['common_name'] = json.get('common_name', '*')
    json['sans'] = json.get('sans', None)
    json['authority'] = json.get('authority', None)
    json['destinations'] = json.get('destinations', None)
    return AttrDict(json)

def renew(args):
    app.logger.info('update.renew:\n{0}'.format(pformat(locals())))
    return {'certs': []}

def deploy(args):
    app.logger.info('update.deploy:\n{0}'.format(pformat(locals())))

    return {'certs': []}

def update(json):
    args = defaults(json)
    if args.authority:
        results = renew(args)
    elif args.destinations:
        results = deploy(args)
    else:
        raise MissingUpdateArgumentsError(args)
    return make_response(jsonify(results), 201)

