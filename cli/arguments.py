#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.arguments: default arguments with the ability to override them
'''

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

# these are the default values for these arguments

    parser.add_argument(
        'common_name',
        metavar='common-name',
        help='common name')
    parser.add_argument(
        '-s', '--sans',
        nargs='+',
        help='default="%(default)s"; add additional sans')
DEFAULTS = {
    ('-s', '--sans'): dict(
        nargs='+',
        help='add additional [s]ubject [a]lternative [n]ame'
    ),
    ('common_name',): dict(
        metavar='common-name',
        help='the commmon-name to be used for the certificate',
    ),
    ('cert_name',): dict(
        metavar='cert-name',
        default='*',
        nargs='*',
        help='default="%(default)s"; <common-name>@<timestamp>; glob expressions '
            'also accepted; if only a common-name is given, ".*" '
            'will be appended',
    ),
    ('-v', '--verbose'): dict(
        metavar='LEVEL',
        dest='verbosity',
        default=0,
        const=1,
        type=int,
        nargs='?',
        help='set verbosity level',
    ),
    ('-a', '--authority'): dict(
        metavar='AUTH',
        default=AUTHORITIES[0],
        choices=AUTHORITIES,
        help='default="%(default)s"; choose authority; "%(choices)s"',
    ),
    ('-a', '--authorities'): dict(
        metavar='AUTH',
        required=True,
        choices=AUTHORITIES,
        nargs='+',
        help='default="%(default)s"; choose authorities; "%(choices)s"',
    ),
    ('-d', '--destinations'): dict(
        metavar='DEST',
        required=True,
        choices=DESTINATIONS,
        nargs='+',
        help='default="%(default)s"; choose destinations; "%(choices)s"',
    ),
    ('-w', '--within'): dict(
        metavar='DAYS',
        default=14,
        type=int,
        help='default="%(default)s"; within number of days from expiring'
    ),
}

# they can be overridden by supplying kwargs to this function
def add_argument(parser, *sig, **overrides):
    parser.add_argument(
        *sig,
        **{k:overrides.get(k, v) for k,v in DEFAULTS[sig].items()})

