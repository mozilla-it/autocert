#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.revoke
'''

from cli.parsers import verbose_parser

def add_parser(subparsers):
    parser = subparsers.add_parser('revoke', parents=[verbose_parser])
    parser.add_argument(
        'common_name',
        help='common name')
    parser.set_defaults(func=do_revoke)

def do_revoke(ns):
    json = {
        'common_name': ns.common_name,
        'authority': ns.authority,
        'destination': ns.destination,
        'verbosity': ns.verbosity,
    }
    print('do_revoke')
