#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.hello_parser
'''

import requests

from cli.output import output

def add_parser(subparsers):
    parser = subparsers.add_parser('hello')
    parser.add_argument(
        'target',
        default='world',
        nargs='?',
        help='default="%(default)s"; greeting')
    parser.set_defaults(func=do_hello)

def do_hello(ns):
    response = requests.get(ns.api_url / 'hello' / ns.target)
    output(response.json())

