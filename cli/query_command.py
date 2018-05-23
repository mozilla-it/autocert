#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.ls
'''

from cli.arguments import add_argument, get_authorities, get_destinations

def add_parser(subparsers, api_config):
    parser = subparsers.add_parser('query')
    subparsers = parser.add_subparsers(
        dest='target',
        title='target',
        description='choose a target to query')
    add_digicert(subparsers, api_config)
    add_zeus(subparsers, api_config)

def add_digicert(subparsers, api_config):
    parser = subparsers.add_parser('digicert')
    add_argument(parser, '-i', '--order-id')
    add_argument(parser, '-r', '--result-detail')
    add_argument(parser, '-c', '--call-detail')
    add_argument(parser, '-v', '--verbose')
    add_argument(parser, '-R', '--is-renewed')
    add_argument(parser, '-s', '--status')
    add_argument(parser, 'domain_name_pns', default='*', nargs='*')

def add_zeus(subparsers, api_config):
    parser = subparsers.add_parser('zeus')
    add_argument(parser, '-c', '--call-detail')
    add_argument(parser, '-v', '--verbose')
    add_argument(parser, 'domain_name_pns', default='*', nargs='*')

