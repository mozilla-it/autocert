#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.renew
'''

from cli.verbose import verbose_parser

def add_parser(subparsers):
    parser = subparsers.add_parser('renew', parents=[verbose_parser])
    parser.add_argument(
        'common_name',
        help='common name')
    parser.set_defaults(func=do_renew)

def do_renew(ns):
    print('do_renew')
