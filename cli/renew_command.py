#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.renew
'''

import requests

from cli.utils.output import output
from cli.arguments import add_argument

def add_parser(subparsers):
    parser = subparsers.add_parser('renew')
    add_argument(parser, '-a', '--authority')
    add_argument(parser, '-d', '--destinations')
    add_argument(parser, '-w', '--within')
    add_argument(parser, '-c', '--calls')
    add_argument(parser, '-v', '--verbose')
    add_argument(parser, 'cert_name_pns')
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

