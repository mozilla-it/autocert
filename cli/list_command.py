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

def transform_certs(certs):
    return [{c.certificate.common_name: c.certificate.valid_till} for c in certs]

def do_list(ns):
    response = requests.get(ns.api_url / 'list/certs')
    if response.status_code == 200:
        obj = response.json()
        ad = AttrDict(obj)
        results = ad.certs
        if not ns.verbose:
            results = transform_certs(ad.certs)
        output(results)
        return
    else:
        print(response)
        print(response.text)
    raise Exception('wtf do_list')

