#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.autocert: provides entry point main().
'''

import os
import imp
import sys
import logging
from json import dumps
from simplejson.errors import JSONDecodeError
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
from cli.utils.dictionary import dictify, head_body
from cli.utils.url import validate
from cli.utils.yaml import yaml_print
from cli.namespace import jsonify
from cli.arguments import add_argument
from cli.utils.fmt import *
from cli.utils import pki
from cli.config import CFG
from cli import requests
from requests.exceptions import ConnectionError

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
        message = fmt('response = {text}', text=response.text)
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

def web_crt(hostname, timeout=0.2):
    import ssl
    import socket
    import requests
    try:
        r = requests.get('https://'+hostname, timeout=0.1) #FIXME: I wish I didn't do this
        if r.status_code in (200, 301, 302, 303, 304):
            with socket.create_connection((hostname, 443), timeout=timeout) as sock:
                ctx = ssl.create_default_context()
                with ctx.wrap_socket(sock, server_hostname=hostname) as sslsock:
                    der = sslsock.getpeercert(True)
                    pem = ssl.DER_cert_to_PEM_cert(der)
                    return pem
    except ConnectionError as ce:
        pass
    except Exception as ex:
        import traceback
        traceback.print_exc()
    return None

def display(ns, json):
    if not hasattr(ns, 'count') or not ns.count:
        json.pop('count', None)
    if ns.verbosity >= 2:
        bundles = []
        for bundle in json['bundles']:
            head, body = head_body(bundle)
            common_name = body['common_name']
            crt_sha1 = body['sha1']
            web = web_crt(common_name)
            verified = False
            if web:
                web_sha1 = pki.get_sha1(web)
                verified = web_sha1 == crt_sha1
            bundle[head]['verified'] = verified
            bundles += [bundle]
        json['bundles'] = bundles
    output_print(json, ns.output)

def do_request(ns):
    method = METHODS[ns.command]
    destinations = dictify(ns.destinations) if hasattr(ns, 'destinations') else None
    json = jsonify(ns, destinations=destinations if destinations else None)
    validate(ns.api_url, throw=True)
    response = requests.request(method, ns.api_url / 'autocert', json=json)
    status = response.status_code
    if status in (200, 201, 202, 203, 204):
        try:
            json = response.json()
            display(ns, json)
        except JSONDecodeError as jde:
            print(jde)
            return -1
    else:
        print('status =', status)
        try:
            output_print(response.json(), ns.output)
        except:
            print('response.text =', response.text)
        return -1
    return 0

def main(args):
    parser = ArgumentParser(
        add_help=False)
    parser.add_argument(
        '--config',
        choices=LOC,
        const=LOC[0],
        nargs='?',
        help='default="%(const)s"; show the config')
    parser.add_argument(
        '--version',
        choices=LOC,
        const=LOC[0],
        nargs='?',
        help='default="%(const)s"; show the version')
    parser.add_argument(
        '--api-url',
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
        '--output',
        metavar='OUPUT',
        default=default_output(),
        choices=OUTPUT,
        help='default="%(default)s"; set the output type; choices=[%(choices)s]')
    parser.add_argument(
        '--timeout',
        metavar='INT',
        default=2,
        help='default="%(default)s"; set the timeout used in connectivity check')

    add_argument(parser, '-n', '--nerf')
    add_argument(parser, '--no-version-check')

    parser.set_defaults(**CFG)
    ns, rem = parser.parse_known_args(args)

    config = AttrDict(
        cli=dict(CFG),
        api=fetch_api_config(ns))
    version = AttrDict(
        cli=get_cli_version(),
        api=fetch_api_version(ns))
    if ns.version_check:
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

    parser.set_defaults(func=do_request)
    add_subparsers(parser, config.api)
    parser.set_defaults(**CFG)

    ns = parser.parse_args(rem)
    if ns.nerf:
        output_print(dict(ns=ns.__dict__), ns.output)
        sys.exit(0)

    return ns.func(ns)
