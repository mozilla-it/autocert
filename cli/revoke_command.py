#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.revoke
'''

from cli.namespace import jsonify
from cli.arguments import add_argument

def add_parser(subparsers):
    parser = subparsers.add_parser('revoke')
    add_argument(parser, '-d', '--destinations')
    add_argument(parser, '-c', '--calls')
    add_argument(parser, '-v', '--verbose')
    add_argument(parser, 'cert_name_pns')
    parser.set_defaults(func=do_revoke)

def do_revoke(ns):
    print('do_revoke')
