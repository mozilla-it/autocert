#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.create
'''

import json
import requests

from cli.utils.output import output
from cli.namespace import jsonify
from cli.arguments import add_argument, get_authorities, get_destinations

from utils.dictionary import dictify

def add_parser(subparsers, api_config):
    parser = subparsers.add_parser('create')
    authorities = get_authorities(**api_config)
    destinations = get_destinations(**api_config)
    add_argument(parser, '-o', '--organization-name')
    add_argument(parser, '-b', '--bug')
    add_argument(parser, '-a', '--authority',
        default=authorities[0],
        choices=authorities)
    add_argument(parser, '-d', '--destinations',
        required=False,
        choices=destinations)
    add_argument(parser, '-s', '--sans')
    add_argument(parser, '-S', '--sans-file')
    add_argument(parser, '-y', '--validity-years')
    add_argument(parser, '--repeat-delta')
    add_argument(parser, '-c', '--calls')
    add_argument(parser, '-n', '--nerf')
    add_argument(parser, '-v', '--verbose')
    add_argument(parser, 'common_name')
