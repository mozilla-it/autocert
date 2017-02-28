#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.renew
'''

import requests

from cli.utils.output import output
from cli.namespace import jsonify
from cli.arguments import add_argument

from utils.dictionary import dictify

def add_parser(subparsers):
    parser = subparsers.add_parser('renew')
    add_argument(parser, '-a', '--authority')
    add_argument(parser, '-d', '--destinations', required=False)
    add_argument(parser, '-w', '--within')
    add_argument(parser, '-c', '--calls')
    add_argument(parser, '-v', '--verbose')
    add_argument(parser, 'cert_name_pns')
    parser.set_defaults(func=do_renew)

def do_renew(ns):
    json = jsonify(ns, destinations=dictify(ns.destinations))
    response = requests.put(ns.api_url / 'autocert', json=json)
    if response.status_code == 201:
        certs = response.json()['certs']
        output(certs)
        return
    else:
        print(response)
        print(response.text)
    raise Exception('wtf do_renew')

