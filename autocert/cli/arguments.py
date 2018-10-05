#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.arguments: default arguments with the ability to override them
'''
import re

from datetime import timedelta

from cli.utils.dictionary import merge
from cli.utils.fmt import *
from cli.config import CFG

CALLS_STYLE = [
    'simple',
    'detail',
]

DETAIL = [
    'summary',
    'detailed'
]

ORGANIZATIONS = [
    'f', 'Mozilla Foundation',
    'c', 'Mozilla Corporation',
]

STATUS_TYPES = [
    'issued',
    'pending',
    'expired',
    'revoked',
    'rejected',
    'canceled',
]

class WrongBugFormatError(Exception):
    def __init__(self, string):
        msg = fmt('WrongBugFormatError: bug should be 7-8 digits long but was, {string}')
        super(WrongBugFormatError, self).__init__(msg)

class WrongPgpFingerprintFormatError(Exception):
    def __init__(self, string):
        msg = fmt('WrongPgpFingerprintFormatError: pgp fingerprint should be 40 hex characters long; {string} does not match')
        super(WrongPgpFingerprintFormatError, self).__init__(msg)

def bug_type(string):
    pattern = '\d{7,8}'
    regex = re.compile(pattern)
    if regex.match(string):
        return string
    raise WrongBugFormatError(string)

def x509_file(path):
    return open(path).read()

def organization_type(string):
    if string == 'f':
        return 'Mozilla Foundation'
    elif string == 'c':
        return 'Mozilla Corporation'
    return string

def pgp_fingerprint(string):
    pattern = '[A-Fa-f0-9]{40}'
    regex = re.compile(pattern)
    if regex.match(string):
        return string
    raise WrongPgpFingerprintFormatError(string)

from argparse import Action

class EncryptAction(Action):
    def __call__(self, parser, namespace, values, option_string=None):
        sign_from = pgp_fingerprint(values[0])
        sign_to = pgp_fingerprint(values[1])
        setattr(namespace, 'sign_from', sign_from)
        setattr(namespace, 'sign_to', sign_to)
        setattr(namespace, 'encrypt', True)

class SansAction(Action):
    def __call__(self, parser, namespace, values, option_string=None):
        sans = getattr(namespace, 'sans', [])
        if option_string in ('-s', '--sans'):
            sans += values
        elif option_string in ('-S', '--sans-file'):
            with open(values) as f:
                sans = [san for san in f.read().strip().split('\n') if not san.startswith('#')]
        setattr(namespace, 'sans', sans)

def get_authorities(authorities=None, **kwargs):
    if authorities is not None:
        return list(authorities.keys())
    return []

def get_destinations(destinations=None, **kwargs):
    d = []
    if destinations is not None:
        for k, v in destinations.items():
            for i in v.keys():
                d += [fmt('{k}:{i}')]
    return d

# these are the default values for these arguments
ARGS = {
    ('-o', '--organization-name'): dict(
        metavar='ORG',
        required=True,
        choices=ORGANIZATIONS,
        type=organization_type,
        help='which organization to take action under; choices=[%(choices)s]'
    ),
    ('-a', '--authority'): dict(
        metavar='AUTH',
        default=None,
        choices=[],
        help='default="%(default)s"; choose authority; choices=[%(choices)s]'
    ),
    ('-a', '--authorities'): dict(
        metavar='AUTH',
        required=True,
        choices=[],
        default=[],
        nargs='+',
        help='default="%(default)s"; choose authorities; choices=[%(choices)s]'
    ),
    ('-d', '--destinations'): dict(
        metavar='DEST',
        required=True,
        choices=[],
        default=[],
        nargs='+',
        help='default="%(default)s"; choose destinations; choices=[%(choices)s]'
    ),
    ('-b', '--bug'): dict(
        required=True,
        type=bug_type,
        const='0000000',
        nargs='?',
        help='the bug number assocated with this ssl|tls certificate'
    ),
    ('-w', '--within'): dict(
        metavar='DAYS',
        default=14,
        type=int,
        help='default="%(default)s"; within number of days from expiring'
    ),
    ('-s', '--sans'): dict(
        default=[],
        action=SansAction,
        nargs='+',
        help='add additional [s]ubject [a]lternative [n]ame(s)'
    ),
    ('-S', '--sans-file'): dict(
        metavar='FILEPATH',
        action=SansAction,
        help='supply a file to add additional [s]ubject [a]lternative [n]ame(s)'
    ),
    ('-y', '--validity-years'): dict(
        metavar='YEARS',
        default=1,
        type=int,
        help='default="%(default)s"; choose number of years for certificate'
    ),
    ('--repeat-delta',): dict(
        dest='repeat_delta',
        metavar='SECS',
        default=90,
        type=int,
        help='default="%(default)s"; repeat delta when getting cert from digicert'
    ),
    ('-c', '--call-detail'): dict(
        const=DETAIL[0],
        choices=DETAIL,
        nargs='?',
        help='const="%(const)s"; toggle and choose the call output format; choices=[%(choices)s]'
    ),
    ('-r', '--result-detail'): dict(
        default=DETAIL[0],
        const=DETAIL[0],
        choices=DETAIL,
        nargs='?',
        help='const="%(const)s"; toggle and choose the detail output format; choices=[%(choices)s]'
    ),
    ('-n', '--nerf'): dict(
        action='store_true',
        help='dry-run or nerf the command'
    ),
    ('-v', '--verbose'): dict(
        metavar='LEVEL',
        dest='verbosity',
        default=0,
        const=1,
        type=int,
        nargs='?',
        help='set verbosity level'
    ),
    ('-i', '--order-id'): dict(
        metavar='ID',
        help='match on order id'
    ),
    ('-R', '--is-renewed'): dict(
        action='store_true',
        help='toggle matching the is_renewed field to true'
    ),
    ('--verify',): dict(
        action='store_true',
        help='force verification with authority'
    ),
    ('--blacklist-overrides',): dict(
        nargs='+',
        metavar='OVERRIDES',
        default=[''],
        help='list of glob expressions to override blacklist behavior'
    ),
    ('--whois-check',): dict(
        action='store_true',
        help='enable the whois check'
    ),
    ('--no-version-check',): dict(
        dest='version_check',
        action='store_false',
        help='toggle version check off'
    ),
    ('--expired',): dict(
        action='store_true',
        help='show expired bundles'
    ),
    ('--count',): dict(
        action='store_true',
        help='add count to bundles|result json|yaml returned from api calls'
    ),
    ('-s', '--status',): dict(
        metavar='STATUS',
        default=[STATUS_TYPES[0]],
        choices=STATUS_TYPES,
        nargs='+',
        help='default=%(default)s; choose which status type(s) to return; choices=[%(choices)s]'
    ),
    ('-K','--key'): dict(
        type=x509_file,
        help='optionally provide key to be used in generating csr and crt; key will be stored in bundle'
    ),
    ('-C','--csr'): dict(
        type=x509_file,
        help='optionally provide csr to be used in generating crt; key will not, but csr will be stored in bundle'
    ),
    ('common_name',): dict(
        metavar='common-name',
        help='the commmon-name to be used for the certificate'
    ),
    ('bundle_name_pns',): dict(
        metavar='bundle-name',
        nargs='+',
        help='default="%(default)s"; <common-name>@<modhash>; glob expressions '
            'also accepted; if only a common-name is given, "*" will be appended'
    ),
    ('domain_name_pns',): dict(
        metavar='domain-name',
        nargs='+',
        help='default="%(default)s"; <domain-name>; glob expressions also accepted'
    ),
    ('bundle_name',): dict(
        metavar='bundle-name',
        help='name of the tar bundle in format <domain>@<hash>.tar.gz'
    ),
    ('-c', '--bundle-host'): dict(
        metavar='bundle-host',
        help='default="%(default)s"; set the host where the tar bundles are stored'
    ),
    ('-e', '--encrypt'): dict(
        dest='from_to',
        metavar=('from', 'to'),
        action=EncryptAction,
        nargs=2,
        help='provide the pgp fingerprint long id <from> and <to> to be used with gpg encrypt and signing; note: will result in encrypted bundle only'
    ),
}

# they can be overridden by supplying kwargs to this function
def add_argument(parser, *sig, **overrides):
    parser.add_argument(
        *sig,
        **merge(ARGS[sig], overrides))

