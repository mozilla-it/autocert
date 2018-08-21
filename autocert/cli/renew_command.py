#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.renew
'''

from cli.arguments import add_argument, get_authorities, get_destinations

def add_parser(subparsers, app_config):
    parser = subparsers.add_parser('renew')
    authorities = get_authorities(**app_config)
    destinations = get_destinations(**app_config)
    add_argument(parser, '-o', '--organization-name')
    add_argument(parser, '-b', '--bug')
    add_argument(parser, '-a', '--authority',
        default=authorities[0],
        choices=authorities)
    add_argument(parser, '-d', '--destinations',
        required=False,
        choices=destinations)
    add_argument(parser, '-s', '--sans', help='sans to ADD to the existing cert(s)')
    add_argument(parser, '-S', '--sans-file', help='file of sans to ADD to the existing cert(s)')
    add_argument(parser, '-y', '--validity-years')
    add_argument(parser, '--repeat-delta')
    add_argument(parser, '--whois-check')
    add_argument(parser, '-w', '--within')
    add_argument(parser, '-c', '--call-detail')
    add_argument(parser, '-v', '--verbose')
    add_argument(parser, '--blacklist-overrides',)
    add_argument(parser, '--count')
    add_argument(parser, 'cert_name_pns')
