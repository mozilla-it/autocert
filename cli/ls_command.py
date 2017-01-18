#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.ls
'''
import requests

from attrdict import AttrDict

from cli.utils.output import output
from cli.utils.dictionary import head, body
from cli.transform import transform
from cli.parsers import verbose_parser, cert_parser

def add_parser(subparsers):
    parser = subparsers.add_parser('ls', parents=[cert_parser, verbose_parser])
    parser.add_argument(
        '-a', '--authorities',
        metavar='AUTH',
        default=['*'],
        nargs='*',
        help='default="%(default)s"; limit search to an authority')
    parser.add_argument(
        '-d', '--destinations',
        metavar='DEST',
        default=['*'],
        nargs='*',
        help='default="%(default)s"; limit search to an authority')
    parser.set_defaults(func=do_ls)

def do_ls(ns):
    json = {
        'cert_name': ns.cert_name,
        'verbosity': ns.verbosity,
        'authorities': ns.authorities,
        'destinations': ns.destinations,
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
    raise Exception('wtf do_ls')

