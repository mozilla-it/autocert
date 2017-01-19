#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.parsers: support class for adding parent parsers
'''

from argparse import ArgumentParser

AUTHORITIES = [
    'digicert',
    'letsencrypt',
]

DESTINATIONS = [

    'zeus:scl3-ext',
    'zeus:scl3-int',
    'zeus:phx1-ext',
    'zeus:phx1-int',
    'zeus:test',
]

def _get_cert_parser(parser, **kwargs):
    parser.add_argument(
        'cert_name',
        metavar=kwargs.get('metavar', 'cert-name'),
        default=kwargs.get('default', '*'),
        nargs=kwargs.get('nargs', '?'),
        help=kwargs.get('help',
            'default="%(default)s"; <common-name>@<timestamp>; glob expressions '
            'also accepted; if only a common-name is given, ".*" '
            'will be appended'))
    return parser

def _get_verbosity_parser(parser, **kwargs):
    parser.add_argument(
        '--verbose',
        metavar=kwargs.get('metavar', 'LEVEL'),
        dest=kwargs.get('dest', 'verbosity'),
        default=kwargs.get('default', 0),
        const=kwargs.get('const', 1),
        type=kwargs.get('type', int),
        nargs=kwargs.get('nargs', '?'),
        help=kwargs.get('help', 'set verbosity level'))
    return parser

def _get_authority_parser(parser, **kwargs):
    parser.add_argument(
        '-a', '--authority',
        metavar=kwargs.get('metavar', 'AUTH'),
        default=kwargs.get('default', 'digicert'),
        choices=kwargs.get('choices', AUTHORITIES),
        help=kwargs.get('help', 'default="%(default)s; choose authority; "%(choices)s"'))
    return parser

def _get_authorities_parser(parser, **kwargs):
    parser.add_argument(
        '-a', '--authorities',
        metavar=kwargs.get('metavar', 'AUTH'),
        required=kwargs.get('required', True),
        choices=kwargs.get('choices', AUTHORITIES),
        nargs=kwargs.get('nargs', '+'),
        help=kwargs.get('help', 'default="%(default)s; choose authorities; "%(choices)s"'))
    return parser

def _get_destinations_parser(parser, **kwargs):
    parser.add_argument(
        '-d', '--destinations',
        metavar=kwargs.get('metavar', 'DEST'),
        required=kwargs.get('required', True),
        choices=kwargs.get('choices', DESTINATIONS),
        nargs=kwargs.get('nargs', '+'),
        help=kwargs.get('help', 'default="%(default)s; choose destinations; "%(choices)s"'))
    return parser

def get(name, **kwargs):
    parser = ArgumentParser(add_help=False)
    if name == 'cert':
        parser = _get_cert_parser(parser, **kwargs)
    elif name == 'verbosity':
        parser = _get_verbosity_parser(parser, **kwargs)
    elif name == 'authority':
        parser = _get_authority_parser(parser, **kwargs)
    elif name == 'authorities':
        parser = _get_authorities_parser(parser, **kwargs)
    elif name == 'destinations':
        parser = _get_destinations_parser(parser, **kwargs)
    return parser

