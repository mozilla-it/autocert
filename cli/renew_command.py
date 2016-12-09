#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.renew
'''

def add_parser(subparsers):
    parser = subparsers.add_parser('renew')
    parser.add_argument(
        'common_name',
        help='common name')
    parser.set_defaults(func=do_renew)

def do_renew(ns):
    print('do_renew')
