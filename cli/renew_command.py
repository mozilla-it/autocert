#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.renew
'''

import requests

from cli.utils.output import output
from cli.verbose import verbose_parser

AUTHORITIES = [
    'digicert',
    'letsencrypt',
]

def add_parser(subparsers):
    parser = subparsers.add_parser('renew', parents=[verbose_parser])
    parser.add_argument(
        'common_name',
        help='common name')
    parser.add_argument(
        '-a', '--authority',
        metavar='AUTH',
        choices=AUTHORITIES,
        default=AUTHORITIES[0],
        help='default="%(default)s"; choose which authority to use')
    parser.set_defaults(func=do_renew)

def do_renew(ns):
    json = {
        'common_name': ns.common_name,
        'authority': ns.authority,
        'verbosity': ns.verbosity,
    }
    response = requests.put(ns.api_url / 'auto-cert', json=json)
    if response.status_code == 201:
        certs = response.json()['certs']
        if not ns.verbose:
            pass
        output(certs)
        return
    else:
        print(response)
        print(response.text)
    raise Exception('wtf do_renew')

