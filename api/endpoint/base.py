#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

from flask import make_response, jsonify

from pprint import pprint, pformat
from attrdict import AttrDict
from fnmatch import fnmatch
from ruamel import yaml
from json import dumps
from flask import jsonify

from tardata import Tardata
from authority.factory import create_authority
from destination.factory import create_destination
from utils.asyncrequests import AsyncRequests
from utils import timestamp

from utils import tar
from utils.format import fmt, pfmt
from utils.dictionary import merge, head, head_body

from cert import visit, simple, abbrev

from app import app
from config import CFG

def default_sorting(cert):
    head, body = head_body(cert)
    return body.get('common_name', '')

def timestamp_sorting(cert):
    head, body = head_body(cert)
    return body.get('timestamp', 0)

def expiry_sorting(cert):
    head, body = head_body(cert)
    return body.get('expiry', 0)

SORTING_FUNCS = dict(
    default=default_sorting,
    timestamp=timestamp_sorting,
    expiry=expiry_sorting)

class EndpointBase(object):
    def __init__(self, cfg, args):
        self.timestamp = timestamp.utcnow()
        self.ar = AsyncRequests()
        self.cfg = AttrDict(cfg)
        self.args = AttrDict(args)
        self.verbosity = self.args.verbosity
        authorities = self.cfg.authorities
        self.authorities = AttrDict({
            a: create_authority(a, self.ar, authorities[a], self.verbosity) for a in authorities
        })
        destinations = self.cfg.destinations
        self.destinations = AttrDict({
            d: create_destination(d, self.ar, destinations[d], self.verbosity) for d in destinations
        })
        self.tardata = Tardata(self.cfg.tar.dirpath, self.verbosity)

    @property
    def calls(self):
        return self.ar.calls

    def execute(self, **kwargs):
        raise NotImplementedError

    def respond(self, json, status):
        return make_response(jsonify(json), status)

    def transform(self, certs):
        sorting_func = SORTING_FUNCS[self.args.sorting]
        certs = sorted(certs, key=sorting_func)
        json = dict(
            certs=[self.transform_cert(cert) for cert in certs],
        )
        if self.args.calls:
            calls = [self.transform_call(call) for call in self.ar.calls]
            json['calls'] = calls
        return json

    def transform_cert(self, cert):
        cert_name, cert_body = head_body(cert)
        if self.verbosity == 0:
            return {cert_name: cert_body.get('expiry', None)}
        elif self.verbosity == 1:
            tardata = head(cert_body['tardata'])
            cert_body['tardata'] = tardata
            return {cert_name: cert_body}
        elif self.verbosity == 2:
            cert = visit(cert, func=simple)
        elif self.verbosity == 3:
            cert = visit(cert, func=abbrev)
        return cert

    def transform_call(self, call):
        name = '{0} {1} {2}'.format(call.recv.status, call.send.method, call.send.url)
        if self.args.calls == 'simple':
            return name
        return {name: dict(send=call.send, recv=call.recv)}

    def sanitize(self, cert_name_pn, ext='.tar.gz'):
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

