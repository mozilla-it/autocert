#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.revoke
'''

from cli.namespace import jsonify
from cli.arguments import add_argument

def add_parser(subparsers):
    parser = subparsers.add_parser('revoke')
    add_argument(parser, '-b', '--bug')
    add_argument(parser, '-a', '--authority')
    #add_argument(parser, '-d', '--destinations', required=False) #FIXME: to be added later
    add_argument(parser, '-c', '--calls')
    add_argument(parser, '-v', '--verbose')
    add_argument(parser, '--blacklist-overrides',)
    add_argument(parser, 'cert_name_pns')
