#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

from pprint import pprint, pformat
from attrdict import AttrDict
from fnmatch import fnmatch
from ruamel import yaml
from flask import jsonify

from autocert import digicert
from autocert import zeus
from utils import tar

from utils.dictionary import merge, head, head_body

from app import app

from config import CFG

from endpoint.base import EndpointBase

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

def transform(cert, verbosity=0):
    cert_name, cert_body = head_body(cert)
    if verbosity == 0:
        authority, auth_body = head_body(cert_body['authority'])
        return {cert_name: auth_body.get('expires', None)}
    elif verbosity == 1:
        tarfile = head(cert_body['tarfile'])
        cert_body['tarfile'] = tarfile
        return {cert_name: cert_body}
    elif verbosity == 2:
        tarfile, filenames = head_body(cert_body['tarfile'])
        cert_body['tarfile'] = {tarfile: {filename: filename[-3:].upper() for filename in filenames}}
        return {cert_name: cert_body}
    elif verbosity == 3:
        tarfile, filenames = head_body(cert_body['tarfile'])
        cert_body['tarfile'] = {tarfile: {filename: content[:60] for filename, content in filenames.items()}}
        return {cert_name: cert_body}
    return cert

class DisplayEndpoint(EndpointBase):
    def __init__(self, cfg, verbosity):
        super(DisplayEndpoint, self).__init__(cfg, verbosity)

    def execute(self, **kwargs):
        cert_name_pns = [sanitize(cert_name_pn) for cert_name_pn in self.args.cert_name_pns]
        certs = self.tardata.get_certdata_from_tarfiles(*cert_name_pns)
        return dict(certs=[transform(cert, self.verbosity) for cert in certs]), 200
