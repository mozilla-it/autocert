#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.ls
'''

from cli.arguments import add_argument, get_authorities, get_destinations

def add_parser(subparsers, api_config):
    parser = subparsers.add_parser('ls')
    authorities = get_authorities(**api_config)
    destinations = get_destinations(**api_config)
    add_argument(parser, '-a', '--authorities',
        required=False,
        default=authorities,
        choices=authorities)
    add_argument(parser, '-d', '--destinations',
        required=False,
        default=destinations,
        choices=destinations)
    add_argument(parser, '-w', '--within', default=None)
    add_argument(parser, '--verify')
    add_argument(parser, '--expired')
    add_argument(parser, '-c', '--call-detail')
    add_argument(parser, '-v', '--verbose')
    add_argument(parser, 'cert_name_pns', default='*', nargs='*')
