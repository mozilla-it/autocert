#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.create
'''

import json
import requests

from cli.output import output

from cli.verbose import verbose_parser

AUTHORITIES = [
    'digicert',
    'letsencrypt',
]

def add_parser(subparsers):
    parser = subparsers.add_parser('create', parents=[verbose_parser])
    parser.add_argument(
        'common_name',
        help='common name')
    parser.add_argument(
        '-a', '--authority',
        metavar='AUTH',
        default=AUTHORITIES[0],
        choices=AUTHORITIES,
        help='default="%(default)s"; choose which authority to use')
    parser.add_argument(
        '-d', '--destination',
        metavar='DEST',
        default='*',
        help='default="%(default)s"; choose which destinations for install')

    parser.set_defaults(func=do_create)

def do_create(ns):
    json = {
        'common_name_pattern': ns.common_name,
        'authority_pattern': ns.authority,
        'destination_pattern': ns.destination,
    }
    response = requests.post(ns.api_url / 'auto-cert', json=json)
    if response.status_code == 201:
        certs = response.json()['certs']
        if not ns.verbose:
            pass
        output(certs)
        return
    else:
        print(response)
        print(response.text)
    raise Exception('wtf do_show')

