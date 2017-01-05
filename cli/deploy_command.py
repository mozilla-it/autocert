#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.deploy
'''

import requests

from cli.utils.output import output
from cli.verbose import verbose_parser

DESTINATIONS = [
    'zeus:scl3-ext',
    'zeus:scl3-int',
    'zeus:phx1-ext',
    'zeus:phx1-int',
    'zeus:test',
]

def add_parser(subparsers):
    parser = subparsers.add_parser('deploy', parents=[verbose_parser])
    parser.add_argument(
        'cert_name',
        help='common_name + suffix')
    parser.add_argument(
        '-d', '--destinations',
        metavar='DEST',
        required=True,
        choices=DESTINATIONS,
        nargs='+',
        help='default="%(default)s"; choose which destinations for install')
    parser.set_defaults(func=do_deploy)

def dictify(destinations, sep=':'):
    result = {}
    for destination in destinations:
        key, value = destination.split(sep)
        result[key] = result.get(key, []) + [value]
    return result

def do_deploy(ns):
    json = {
        'cert_name': ns.cert_name,
        'destinations': dictify(ns.destinations),
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
    raise Exception('wtf do_deploy')

