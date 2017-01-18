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
from cli import parsers

def add_parser(subparsers):
    parser = subparsers.add_parser('ls', parents=[
        parsers.get('verbosity'),
        parsers.get('authorities'),
        parsers.get('destinations'),
        parsers.get('cert'),
    ])
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

