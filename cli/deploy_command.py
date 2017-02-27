#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.deploy
'''

import requests

from cli.utils.output import output
from cli.namespace import jsonify
from cli.arguments import add_argument

from utils.dictionary import dictify

def add_parser(subparsers):
    parser = subparsers.add_parser('deploy')
    add_argument(parser, '-d', '--destinations')
    add_argument(parser, '-c', '--calls')
    add_argument(parser, '-v', '--verbose')
    add_argument(parser, 'cert_name_pns')
    parser.set_defaults(func=do_deploy)

def do_deploy(ns):
    json = jsonify(ns, destinations=dictify(ns.destinations))
    response = requests.put(ns.api_url / 'autocert', json=json)
    if response.status_code in (200, 201):
        certs = response.json().get('certs', [])
        output(certs)
    else:
        print(response)
        print(response.text)
        raise Exception('wtf do_deploy')

