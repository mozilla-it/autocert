#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.create
'''

import requests

from cli.output import output

AUTHORITIES = [
    'digicert',
    'letsencrypt',
]

def add_parser(subparsers):
    parser = subparsers.add_parser('create')
    parser.add_argument(
        'common_name',
        help='common name')
    parser.add_argument(
        '--authority',
        default=AUTHORITIES[0],
        choices=AUTHORITIES,
        help='default=%(default)s; choose which authority to use')
    parser.set_defaults(func=do_create)

def do_create(ns):
    url = ns.api_url / 'create' / ns.authority / ns.common_name
    response = requests.put(url)
    print('response.status_code =', response.status_code)
    print('response.text =', response.text)
    if response.status_code != 200:
        output({'error': {'status_code': response.status_code}})
        return
    output(response.json())
