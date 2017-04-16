#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.renew
'''

import requests

from cli.utils.output import output
from cli.namespace import jsonify
from cli.arguments import add_argument

from utils.dictionary import dictify

def add_parser(subparsers):
    parser = subparsers.add_parser('renew')
    add_argument(parser, '-a', '--authority')
    add_argument(parser, '-d', '--destinations', required=False)
    add_argument(parser, '-s', '--sans')
    add_argument(parser, '-y', '--validity-years')
    add_argument(parser, '--repeat-delta')
    add_argument(parser, '-w', '--within')
    add_argument(parser, '-c', '--calls')
    add_argument(parser, '-v', '--verbose')
    add_argument(parser, 'cert_name_pns')
