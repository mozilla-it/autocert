#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.list_parser
'''
import requests

from attrdict import AttrDict

from cli.output import output

def add_parser(subparsers):
    parser = subparsers.add_parser('list')
    parser.add_argument(
        'common_name',
        default='*',
        nargs='?',
        help='default="%(default)s"; common name pattern')
    parser.add_argument(
        '-a', '--authority',
        default='*',
        help='default="%(default)s"; limit search to an authority')
    parser.set_defaults(func=do_list)

class DictHasNoHeadError(Exception):
    def __init__(self, d):
        msg = 'dict has no head: d={0}'.format(d)
        super(DictHasNoHeadError, self).__init__(msg)

def head(d):
    keys = list(d.keys())
    if len(keys) == 1:
        return keys[0]
    raise DictHasNoHeadError(d)

def body(d):
    return d[head(d)]

def transform_certs(certs):
    return [{head(cert): body(cert)['valid_till']} for cert in certs]

def do_list(ns):
    response = requests.get(ns.api_url / 'list/certs')
    if response.status_code == 200:
        certs = response.json()['certs']
        if not ns.verbose:
            certs = transform_certs(certs)
        output(certs)
        return
    else:
        print(response)
        print(response.text)
    raise Exception('wtf do_list')

