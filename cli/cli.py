#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.autocert: provides entry point main().
'''

import os
import imp
import sys
import logging
from json import JSONDecodeError, dumps
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

from cli.utils.importer import import_modules
from cli.utils.version import get_version as get_cli_version
from utils.dictionary import dictify
from utils.url import validate
from cli.utils.yaml import yaml_print
from cli.utils.format import fmt, pfmt
from cli.namespace import jsonify
from cli import requests
from cli.arguments import add_argument

from cli.config import CFG

LOC = [
    'cli',
    'api'
]

SORTING = [
    'default',
    'timestamp',
    'expiry',
]

METHODS = {
    'ls': 'GET',
    'query': 'GET',
    'create': 'POST',
    'renew': 'PUT',
    'deploy': 'PUT',
    'revoke': 'DELETE',
}

OUTPUT = [
    'json',
    'yaml',
]

class VersionCheckFailedError(Exception):
    def __init__(self, required, version):
        message = fmt('autocert/api {version} is not at least {required}')
        super(VersionCheckFailedError, self).__init__(message)

class FetchApiConfigError(Exception):
    def __init__(self, response):
        message = fmt('response = {response}')
        super(FetchApiConfigError, self).__init__(message)

def default_output():
    return OUTPUT[int(sys.stdout.isatty())]

def output_print(json, output):
    if output == 'yaml':
        yaml_print(json)
    elif output == 'json':
        print(dumps(json, indent=2))

def fetch_api_version(ns):
    api_version = 'unknown'
    response = requests.get(ns.api_url / 'autocert/version')
    if response.status_code == 200:
        obj = response.json()
        api_version = obj['version']
    return api_version

def version_check(version):
    if version_parse(version.api) >= version_parse(version.cli):
        logging.debug('version_check: PASSED')
    else:
        raise VersionCheckFailedError(version.cli, version.api)

def fetch_api_config(ns):
    response = requests.get(ns.api_url / 'autocert/config')
    if response.status_code == 200:
        obj = response.json()
        return obj['config']
    raise FetchApiConfigError(response)

def add_subparsers(parser, api_config):
    '''
    add all files that end with _parser.py in the cli/ directory
    call 'add_parser', passing subparsers to each found module
    '''
    subparsers = parser.add_subparsers(
        dest='command',
        title='commands',
        description='choose a command to run')
    dirpath = os.path.dirname(__file__)
    endswith = '_command.py'
    [mod.add_parser(subparsers, api_config) for mod in import_modules(dirpath, endswith)]
    subparsers.required = True
    return subparsers

def do_request(ns):
    method = METHODS[ns.command]
    destinations = dictify(ns.destinations) if hasattr(ns, 'destinations') else None
    json = jsonify(ns, destinations=destinations if destinations else None)
    validate(ns.api_url, throw=True)
    response = requests.request(method, ns.api_url / 'autocert', json=json)
    status = response.status_code
    try:
        json = response.json()
        if not hasattr(ns, 'count') or not ns.count:
            json.pop('count', None)
        output_print(json, ns.output)
    except JSONDecodeError as jde:
        print('status =', status)
        print('JSONDecodeError =', jde)
        print('text =', response.text)
        return -1
    return status

def main():
    parser = ArgumentParser(
        add_help=False)
    parser.add_argument(
        '-C', '--config',
        choices=LOC,
        const=LOC[0],
        nargs='?',
        help='default="%(const)s"; show the config')
    parser.add_argument(
        '-V', '--version',
        choices=LOC,
        const=LOC[0],
        nargs='?',
        help='default="%(const)s"; show the version')
    parser.add_argument(
        '-U', '--api-url',
        metavar='URL',
        default='http://0.0.0.0',
        type=URL,
        help='default="%(default)s"; set the api url to use')
    parser.add_argument(
        '--sort',
        dest='sorting',
        metavar='SORT',
        default=SORTING[0],
        choices=SORTING,
        help='default="%(default)s"; set the sorting method; choices=[%(choices)s]')
    parser.add_argument(
        '-O', '--output',
        metavar='OUPUT',
        default=default_output(),
        choices=OUTPUT,
        help='default="%(default)s"; set the output type; choices=[%(choices)s]')
    parser.add_argument(
        '-T', '--timeout',
        metavar='INT',
        default=2,
        help='default="%(default)s"; set the timeout used in connectivity check')

    add_argument(parser, '-n', '--nerf')

    parser.set_defaults(**CFG)
    ns, rem = parser.parse_known_args()

    config = AttrDict(
        cli=dict(CFG),
        api=fetch_api_config(ns))
    version = AttrDict(
        cli=get_cli_version().split('-')[0],
        api=fetch_api_version(ns))
    version_check(version)

    if ns.version:
        output_print({'{version}-version'.format(**ns.__dict__): version[ns.version]}, ns.output)
        sys.exit(0)
    if ns.config:
        output_print({'{config}-config'.format(**ns.__dict__): config[ns.config]}, ns.output)
        sys.exit(0)

    parser = ArgumentParser(
        parents=[parser],
        description=__doc__,
        formatter_class=RawDescriptionHelpFormatter)

    add_subparsers(parser, config.api)
    parser.set_defaults(**CFG)

    ns = parser.parse_args()
    if ns.nerf:
        output_print(dict(ns=ns.__dict__), ns.output)
        sys.exit(0)

    status = do_request(ns)

    if status not in (200, 201, 202, 203, 204, 205):
        return status
