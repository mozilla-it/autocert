#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.create
'''

def add_parser(subparsers):
    parser = subparsers.add_parser('create')
    parser.add_argument(
        'common_name',
        help='common name')
