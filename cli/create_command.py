#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.create
'''

import json
import requests

from cli.utils.output import output
from cli.namespace import jsonify
from cli.arguments import add_argument

from utils.dictionary import dictify

def add_parser(subparsers):
    parser = subparsers.add_parser('create')
    add_argument(parser, '-o', '--organization-name')
    add_argument(parser, '-a', '--authority')
    add_argument(parser, '-d', '--destinations', required=False)
    add_argument(parser, '-s', '--sans')
    add_argument(parser, '--repeat-delta')
    add_argument(parser, '-c', '--calls')
    add_argument(parser, '-v', '--verbose')
    add_argument(parser, 'common_name')
    parser.set_defaults(func=do_create)

def do_create(ns):
    json = jsonify(ns, destinations=dictify(ns.destinations))
    response = requests.post(ns.api_url / 'autocert', json=json)
    if response.status_code == 201:
        json = response.json()
        output(json)
        return
    else:
        print(response)
        print(response.text)
    raise Exception('wtf do_create')

