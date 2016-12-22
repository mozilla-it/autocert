#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.deploy
'''

from pprint import pformat

def add_parser(subparsers):
    parser = subparsers.add_parser('deploy')
    parser.add_argument(
        'common_name',
        help='common name')
    parser.add_argument(
        '-d', '--destinations',
        metavar='DEST',
        default='zeus',
        nargs='+',
        help='default=%(default)s; 1 or more desinations')

    parser.set_defaults(func=do_renew)

def do_renew(ns):
    print('do_renew:', pformat(ns.__dict__))
