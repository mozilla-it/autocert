#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""cli.cli: provides entry point main()."""

import os
import sys
import logging
import requests

from ruamel import yaml
from urlpath import URL
from attrdict import AttrDict
from subprocess import check_output
from packaging.version import parse as version_parse
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from utils.version import version as cli_version

VERSIONS = [
    'cli',
    'api'
]

ACTIONS = [
    'list',
]

def yaml_format(obj):
    class MyDumper(yaml.Dumper):
        def represent_mapping(self, tag, mapping, flow_style=False):
            return yaml.Dumper.represent_mapping(self, tag, mapping, flow_style)
    return yaml.dump(obj, Dumper=MyDumper).strip()

class VersionCheckFailedError(Exception):
    def __init__(self, version, required):
        msg = 'auto-cert/api {version} is not at least {required}'.format(**locals())
        super(VersionCheckFailedError, self).__init__(msg)

def api_version(ns):
    response = requests.get(ns.api_url / 'version')
    version = 'unknown'
    if response.status_code == 200:
        version = response.json()['version']
    return version

def version_check(ns):
    if ns.version not in VERSIONS:
        version = api_version(ns)
        version = version.split('-')[0]
        if  version_parse(version) >= version_parse(cli_version()):
            logging.debug('version_check: PASSED')
            return
        raise VersionCheckFailedError(version, cli_version())
    if ns.version == VERSIONS[0]:
        print(yaml_format({'cli-version': cli_version()}))
    elif ns.version == VERSIONS[1]:
        print(yaml_format({'api-version': api_version(ns)}))
    sys.exit(0)

def hello(ns):
    response = requests.get(ns.api_url / 'hello' / ns.target)
    print(yaml_format(response.json()))

def transform_certs(certs):
    return [ {c.certificate.common_name: c.certificate.valid_till} for c in certs ]

def certs(ns):
    if ns.action == 'list':
        response = requests.get(ns.api_url / 'certs/list')
        ad = AttrDict(response.json())
        if ns.verbose:
            output = dict(ad)['certs']
        else:
            output = transform_certs(ad.certs)
        print(yaml_format(output))

def main():
    cli_parser = ArgumentParser(
        add_help=False)
    cli_parser.add_argument(
        '--debug',
        action='store_true',
        help='turn on debug mode')
    cli_parser.add_argument(
        '--version',
        choices = VERSIONS,
        const=VERSIONS[0],
        nargs='?',
        help='default=%(const)s show the version')
    cli_parser.add_argument(
        '--verbose',
        action='store_true',
        help='more verbose output')
    cli_parser.add_argument(
        '--api-url',
        metavar='URL',
        type=URL,
        default=r'http://0.0.0.0',
        help='default=%(default)s set the api url to use')

    ns, _ = cli_parser.parse_known_args()
    version_check(ns)

    config = {}

    cli_parser = ArgumentParser(
        parents=[cli_parser],
        description=__doc__,
        formatter_class=RawDescriptionHelpFormatter,
        argument_default=config)

    cli_subparsers = cli_parser.add_subparsers(
        dest='command',
        title='commands',
        description='commands desc',
        help='choose a command to run')
    cli_subparsers.required = True

    hello_parser = cli_subparsers.add_parser('hello')
    hello_parser.add_argument(
        'target',
        default='',
        nargs='?',
        help='default="%(default)s"')
    hello_parser.set_defaults(func=hello)

    certs_parser = cli_subparsers.add_parser('certs')
    certs_parser.add_argument(
        'action',
        default=ACTIONS[0],
        choices=ACTIONS,
        help='default="%(default)s"')
    certs_parser.set_defaults(func=certs)


    ns = cli_parser.parse_args()
    if ns.debug:
        print('ns =', ns)
    ns.func(ns)
