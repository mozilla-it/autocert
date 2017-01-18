#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.cert
'''

from argparse import ArgumentParser

verbose_parser = ArgumentParser(add_help=False)
verbose_parser.add_argument(
    '--verbose',
    metavar='LEVEL',
    dest='verbosity',
    default=0,
    const=1,
    type=int,
    nargs='?',
    help='set verbosity level')

cert_parser = ArgumentParser(add_help=False)
cert_parser.add_argument(
    'cert_name',
    metavar='cert-name',
    default='*',
    nargs='?',
    help=(
        'default="%(default)s"; <common-name>.<suffix>; glob expressions '
        'also accepted; if only a common-name is given, ".*" '
        'will be appended'))

