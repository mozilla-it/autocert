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
from cli.arguments import add_argument

def add_parser(subparsers):
    parser = subparsers.add_parser('deploy')
    add_argument(parser, '-v', '--verbose')
    add_argument(parser, '-d', '--destinations')
    add_argument(parser, 'cert_name')
    add_argument(parser, '-w', '--within')
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

