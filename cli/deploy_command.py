#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.deploy
'''

import requests

from cli.utils.output import output
from cli.namespace import jsonify
from cli.arguments import add_argument

from utils.dictionary import dictify

def add_parser(subparsers, api_config):
    parser = subparsers.add_parser('deploy')
    add_argument(parser, '-b', '--bug')
    add_argument(parser, '-d', '--destinations')
    add_argument(parser, '-c', '--calls')
    add_argument(parser, '-v', '--verbose')
    add_argument(parser, '--blacklist-overrides',)
    add_argument(parser, 'cert_name_pns')
