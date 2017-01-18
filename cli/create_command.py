#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.create
'''

import json
import requests

from cli.utils.output import output
from cli.transform import transform
from cli import parsers

def add_parser(subparsers):
    parser = subparsers.add_parser('create', parents=[
        parsers.get('verbosity'),
        parsers.get('authority'),
        parsers.get('destinations'),
    ])
    parser.add_argument(
        'common_name',
        metavar='common-name',
        help='common name')
    parser.add_argument(
        '-s', '--sans',
        nargs='+',
        help='default="%(default)s"; add additional sans')

    parser.set_defaults(func=do_create)

def do_create(ns):
    json = {
        'common_name': ns.common_name,
        'authority': ns.authority,
        'sans': ns.sans,
        'verbosity': ns.verbosity,
    }
    response = requests.post(ns.api_url / 'auto-cert', json=json)
    if response.status_code == 201:
        certs = response.json()['certs']
        xformd = transform(certs, ns.verbosity)
        output(xformd)
        return
    else:
        print(response)
        print(response.text)
    raise Exception('wtf do_create')

