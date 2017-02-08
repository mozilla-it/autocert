#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.ls
'''
import requests

from attrdict import AttrDict

from cli.utils.output import output
from cli.namespace import jsonify
from cli.arguments import add_argument

def add_parser(subparsers):
    parser = subparsers.add_parser('ls')
    add_argument(parser, '-a', '--authorities', required=False, default=[])
    add_argument(parser, '-d', '--destinations', required=False, default=[])
    add_argument(parser, '--verify')
    add_argument(parser, '-c', '--calls')
    add_argument(parser, '-v', '--verbose')
    add_argument(parser, 'cert_name_pns')
    parser.set_defaults(func=do_ls)

def do_ls(ns):
    json = jsonify(ns)
    response = requests.get(ns.api_url / 'autocert', json=json)
    if response.status_code == 200:
        json = response.json()
        output(json)
        return
    else:
        print(response)
        print(response.text)
    raise Exception('wtf do_ls')

