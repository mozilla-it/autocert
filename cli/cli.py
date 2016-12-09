#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.cli: provides entry point main().
'''

import os
import imp
import sys
import logging
import requests

from subprocess import check_output
from argparse import ArgumentParser, RawDescriptionHelpFormatter

try:
    from ruamel import yaml
    from urlpath import URL
    from attrdict import AttrDict
    from packaging.version import parse as version_parse
except ImportError as ie:
    print(ie)
    print('perhaps you need to install cli/requirements.txt via pip3')

from cli.utils.version import version as cli_version
from cli.output import output

VERSIONS = [
    'cli',
    'api'
]

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
        output({'cli-version': cli_version()})
    elif ns.version == VERSIONS[1]:
        output({'api-version': api_version(ns)})
    sys.exit(0)

def add_subparsers(parser):
    '''
    add all files that end with _parser.py in the cli/ directory
    call 'add_parser', passing subparsers to each found module
    '''
    subparsers = parser.add_subparsers(
        dest='command',
        title='commands',
        description='choose a command to run')
    commands_path = os.path.dirname(__file__)
    for filename in [f for f in os.listdir(commands_path) if f.endswith('_command.py')]:
        command = imp.load_source(filename.split('.')[0], commands_path+'/'+filename)
        command.add_parser(subparsers)
    subparsers.required = True
    return subparsers

def main():
    parser = ArgumentParser(
        add_help=False)
    parser.add_argument(
        '--debug',
        action='store_true',
        help='turn on debug mode')
    parser.add_argument(
        '--version',
        choices = VERSIONS,
        const=VERSIONS[0],
        nargs='?',
        help='default=%(const)s show the version')
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='more verbose output')
    parser.add_argument(
        '--api-url',
        metavar='URL',
        type=URL,
        default=r'http://0.0.0.0',
        help='default=%(default)s set the api url to use')

    ns, rem = parser.parse_known_args()
    if not any([h in rem for h in ('-h', '--help')]):
        version_check(ns)

    config = {}

    parser = ArgumentParser(
        parents=[parser],
        description=__doc__,
        formatter_class=RawDescriptionHelpFormatter,
        argument_default=config)

    add_subparsers(parser)

    ns = parser.parse_args()
    if ns.debug:
        print('ns =', ns)
    ns.func(ns)
