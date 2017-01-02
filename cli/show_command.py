#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.list_parser
'''
import requests

from attrdict import AttrDict

from cli.output import output
from cli.utils.dictionary import head, body

def add_parser(subparsers):
    parser = subparsers.add_parser('show')
    parser.add_argument(
        'common_name',
        default='*',
        nargs='?',
        help='default="%(default)s"; common name pattern')
    parser.add_argument(
        '-a', '--authority',
        metavar='AUTH',
        default='*',
        help='default="%(default)s"; limit search to an authority')
    parser.add_argument(
        '-d', '--destination',
        metavar='DEST',
        default='*',
        help='default="%(default)s"; limit search to an authority')
    parser.set_defaults(func=do_show)

def transform_certs(certs):
    return [{head(cert): body(cert)['expires']} for cert in certs]

def do_show(ns):
    json = {
        'common_name_pattern': ns.common_name,
        'authority_pattern': ns.authority,
        'destination_pattern': ns.destination,
    }
    response = requests.get(ns.api_url / 'auto-cert', json=json)
    if response.status_code == 200:
        certs = response.json()['certs']
        if not ns.verbose:
            certs = transform_certs(certs)
        output(certs)
        return
    else:
        print(response.status_code)
        print(response)
        print(response.text)
    raise Exception('wtf do_show')

