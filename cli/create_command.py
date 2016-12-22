#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.create
'''

import json
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
    parser.add_argument(
        '--sans',
        nargs='+',
        help='list of subject alternate names')

    parser.set_defaults(func=do_create)

def do_create(ns):
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        'sans': ns.sans,
    }
    url = ns.api_url / 'create' / ns.authority / ns.common_name
    response = requests.put(url, headers=headers, data=json.dumps(data))
    print('response.status_code =', response.status_code)
    print('response.text =', response.text)
    if response.status_code != 200:
        output({'error': {'status_code': response.status_code}})
        return
    output(response.json())
