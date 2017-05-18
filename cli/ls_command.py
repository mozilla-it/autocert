#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.ls
'''
import requests

from attrdict import AttrDict

from cli.utils.output import output
from cli.arguments import add_argument

from cli.config import CFG

def add_parser(subparsers):
    parser = subparsers.add_parser('ls')
    add_argument(parser, '-a', '--authorities', required=False, default=[]) #FIXME: should be similar to DESTINATIONS
    add_argument(parser, '-d', '--destinations', required=False, default=CFG.DESTINATIONS)
    add_argument(parser, '--verify')
    add_argument(parser, '--expired')
    add_argument(parser, '-c', '--calls')
    add_argument(parser, '-v', '--verbose')
    add_argument(parser, 'cert_name_pns', default='*', nargs='*')
