#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.list_parser
'''
import requests

from attrdict import AttrDict

from cli.utils.output import output
from cli.utils.dictionary import head, body
from cli.verbose import verbose_parser
from cli.transform import transform

def add_parser(subparsers):
    parser = subparsers.add_parser('show', parents=[verbose_parser])
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

def do_show(ns):
    json = {
        'common_name': ns.common_name,
    }
    response = requests.get(ns.api_url / 'auto-cert', json=json)
    if response.status_code == 200:
        certs = response.json()['certs']
        xformd = transform(certs, ns.verbosity)
        output(xformd)
        return
    else:
        print(response)
        print(response.text)
    raise Exception('wtf do_show')

