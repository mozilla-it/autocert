#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.deploy
'''

import requests

from cli.utils.output import output
from cli.transform import transform
from cli import parsers
from cli.namespace import jsonify

def add_parser(subparsers):
    parser = subparsers.add_parser('deploy', parents=[
        parsers.get('verbosity'),
        parsers.get('destinations'),
        parsers.get('cert'),
    ])
    parser.add_argument(
        '-w', '--within',
        metavar='DAYS',
        default=14,
        type=int,
        help='default="%(default)s"; within number of days from expiring')
    parser.set_defaults(func=do_deploy)

def dictify(destinations, sep=':'):
    result = {}
    for destination in destinations:
        key, value = destination.split(sep)
        result[key] = result.get(key, []) + [value]
    return result

def do_deploy(ns):
    response = requests.put(ns.api_url / 'auto-cert', json=jsonify(ns, destinations=dictify(ns.destinations)))
    if response.status_code == 200:
        certs = response.json().get('certs', [])
        xformd = transform(certs, ns.verbosity)
        output(xformd)
    elif response.status_code == 201:
        certs = response.json().get('certs', [])
        xformd = transform(certs, ns.verbosity)
        output(xformd)
    else:
        print(response)
        print(response.text)
        raise Exception('wtf do_deploy')

