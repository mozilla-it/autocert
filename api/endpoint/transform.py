#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

from json import dumps

from pprint import pprint, pformat
from attrdict import AttrDict
from fnmatch import fnmatch
from ruamel import yaml
from flask import jsonify

from autocert import digicert
from autocert import zeus
from utils import tar
from utils.format import fmt, pfmt
from utils.dictionary import merge, head, head_body

from app import app

from config import CFG

def sanitize(cert_name_pn, ext='.tar.gz'):
    if cert_name_pn.endswith(ext):
        cert_name_pn = cert_name_pn[0:-len(ext)]
    cert_name_pn = os.path.basename(cert_name_pn)
    regex = re.compile('([A-Za-z0-9\.\-_]+)(@([0-9]{14}))?')
    match = regex.search(cert_name_pn)
    if match:
        common_name, _, timestamp = match.groups()
        if timestamp:
            return cert_name_pn
        if common_name.endswith('*'):
            return common_name
        return common_name + '*'
    return cert_name_pn

def callify(call, style):
    if style == 'simple':
        return '{0} {1} {2}'.format(call.recv.status, call.send.method, call.send.url)
    return dict(send=call.send, recv=call.recv)

def transform(cert, verbosity=0):
    cert_name, cert_body = head_body(cert)
    if verbosity == 0:
        authority, auth_body = head_body(cert_body['authority'])
        return {cert_name: auth_body.get('expires', None)}
    elif verbosity == 1:
        tardata = head(cert_body['tardata'])
        cert_body['tardata'] = tardata
        return {cert_name: cert_body}
    elif verbosity == 2:
        tardata, filenames = head_body(cert_body['tardata'])
        cert_body['tardata'] = {tardata: {filename: filename[-3:].upper() for filename in filenames}}
        return {cert_name: cert_body}
    elif verbosity == 3:
        tardata, filenames = head_body(cert_body['tardata'])
        cert_body['tardata'] = {tardata: {filename: content[:60] for filename, content in filenames.items()}}
        return {cert_name: cert_body}
    return cert

