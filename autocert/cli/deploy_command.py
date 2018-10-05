#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.deploy
'''

from cli.arguments import add_argument, get_authorities, get_destinations

def add_parser(subparsers, api_config):
    parser = subparsers.add_parser('deploy')
    destinations = get_destinations(**api_config)
    add_argument(parser, '-b', '--bug')
    add_argument(parser, '-d', '--destinations',
        required=False,
        choices=destinations)
    add_argument(parser, '-c', '--call-detail')
    add_argument(parser, '-v', '--verbose')
    add_argument(parser, '--blacklist-overrides',)
    add_argument(parser, '--count',)
    add_argument(parser, 'bundle_name_pns')
