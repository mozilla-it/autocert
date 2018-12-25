#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.fetch
'''

import os
from urllib.parse import urlparse

from cli.arguments import add_argument
from cli.utils.shell import call
from cli.config import CFG

def do_fetch(ns):
    bundle_path = '/data/autocert/bundles'
    src = f'{ns.bundle_host}:{ns.bundle_path}/{ns.bundle_name}'
    dst = os.getcwd()
    exitcode, out, err = call(f'rsync -avP --rsync-path="sudo rsync" "{src}" "{dst}"', throw=True)
    if ns.encrypt:
        call(f'gpg -u "{ns.sign_from}" -r "{ns.sign_to}" --sign --encrypt "{ns.bundle_name}"', throw=True)
        tar_bundle = os.path.join(dst, ns.bundle_name)
        gpg_file = tar_bundle + '.gpg'
        if os.path.isfile(gpg_file):
            os.remove(tar_bundle)
            print('removed', tar_bundle)

def add_parser(subparsers, api_config):
    parser = subparsers.add_parser('fetch')
    add_argument(parser, '-c', '--bundle-host', default=urlparse(CFG.api_url).hostname)
    add_argument(parser, '-e', '--encrypt')
    add_argument(parser, 'bundle_name')
    parser.set_defaults(func=do_fetch)
