#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
utils.cert
'''

import os
import copy

from utils import tar
from utils.fmt import *
from utils.isinstance import *

from utils.yaml import yaml_format, yaml_print
from utils.dictionary import head, body, head_body, keys_ending
from utils.exceptions import AutocertError

from pprint import pprint
from datetime import datetime

DIRPATH = os.path.dirname(os.path.abspath(__file__))

class CertFromJsonError(AutocertError):
    def __init__(self, ex):
        message = 'cert.from_json error'
        super(CertFromJsonError, self).__init__(message)
        self.errors = [ex]

class CertLoadError(AutocertError):
    def __init__(self, tarpath, cert_name, ex):
        message = fmt('error loading {cert_name}.tar.gz from {tarpath}')
        super(CertLoadError, self).__init__(message)
        self.errors = [ex]

class VisitError(AutocertError):
    def __init__(self, obj):
        message = fmt('unknown type obj = {obj}')
        super(VisitError, self).__init__(message)

def printit(obj):
    print(obj)
    return obj

def simple(obj):
    if istuple(obj):
        key, value = obj
        if isinstance(value, str) and key[-3:] in ('crt', 'csr', 'key'):
            value = key[-3:].upper()
        return key, value
    return obj

def abbrev(obj):
    if istuple(obj):
        key, value = obj
        if isinstance(value, str) and key[-3:] in ('crt', 'csr', 'key'):
            lines = value.split('\n')
            lines = lines[:2] + ['...'] + lines[-3:]
            value = '\n'.join(lines)
        return key, value
    return obj

def visit(obj, func=printit):
    obj1 = None
    if isdict(obj):
        obj1 = {}
        for key, value in obj.items():
            if isscalar(value):
                key1, value1 = visit((key, value), func=func)
            else:
                key1 = key
                value1 = visit(value, func=func)
            obj1[key1] = value1
    elif islist(obj):
        obj1 = []
        for item in obj:
            obj1.append(visit(item, func=func))
    elif isscalar(obj) or istuple(obj) and len(obj) == 2:
        obj1 = func(obj)
    elif isinstance(obj, datetime):
        obj1 = func(obj)
    else:
        raise VisitError(obj)
    return obj1

class Cert(object):

    def __init__(self, common_name, timestamp, modhash, key, csr, crt, bug, sans=None, expiry=None, authority=None, destinations=None):
        if authority:
            assert isinstance(authority, dict)
        self.common_name    = common_name
        self.timestamp      = timestamp
        self.modhash        = modhash
        self.key            = key
        self.csr            = csr
        self.crt            = crt
        self.bug            = bug
        self.sans           = sans
        self.expiry         = expiry
        self.authority      = authority
        self.destinations   = destinations if destinations else {}

        with open(DIRPATH + '/README.tarfile') as f:
            self.readme = f.read()

    def __repr__(self):
        return yaml_format(self.to_json())

    def __eq__(self, cert):
        return (
            self.common_name == cert.common_name and
            self.timestamp == cert.timestamp and
            self.modhash == cert.modhash and
            self.key == cert.key and
            self.csr == cert.csr and
            self.crt == cert.crt and
            self.bug == cert.bug and
            self.sans == cert.sans and
            self.expiry == cert.expiry and
            self.authority == cert.authority)

    @staticmethod
    def _decompose(cert, tardata=False):
        try:
            cert_name, cert_body = head_body(cert)
            common_name = cert_body['common_name']
            timestamp = cert_body['timestamp']
            modhash = cert_body['modhash']
            expiry = cert_body['expiry']
            authority = cert_body['authority']
            bug = cert_body.get('bug', None)
            sans = cert_body.get('sans', None)
            destinations = cert_body.get('destinations', None)
            if tardata:
                files = cert_body['tardata'][fmt('{cert_name}.tar.gz')]
                key = files[fmt('{cert_name}.key')]
                csr = files[fmt('{cert_name}.csr')]
                crt = files[fmt('{cert_name}.crt')]
            else:
                key, csr, crt = [None] * 3
        except KeyError as ke:
            print(ke)
            pprint(cert)
            raise CertFromJsonError(ke)
        return common_name, timestamp, modhash, key, csr, crt, bug, sans, expiry, authority, destinations

    @staticmethod
    def load(tarpath, cert_name):
        key, csr, crt, yml, readme = tar.unbundle(tarpath, cert_name)
        try:
            common_name, timestamp, modhash, _, _, _, bug, sans, expiry, authority, destinations = Cert._decompose(yml)
        except AutocertError as ae:
            raise CertLoadError(tarpath, cert_name, ae)

        return Cert(
            common_name,
            timestamp,
            modhash,
            key,
            csr,
            crt,
            bug,
            sans,
            expiry,
            authority,
            destinations)

    @staticmethod
    def from_json(json):
        common_name, timestamp, modhash, key, csr, crt, bug, sans, expiry, authority, destinations = Cert._decompose(json, True)
        return Cert(
            common_name,
            timestamp,
            modhash,
            key,
            csr,
            crt,
            bug,
            sans,
            expiry,
            authority,
            destinations)

    @property
    def modhash_abbrev(self):
        return self.modhash[:8]

    @property
    def friendly_common_name(self):
        if self.common_name.startswith('*.'):
            return 'wildcard' + self.common_name[1:]
        return self.common_name

    @property
    def cert_name(self):
        return self.friendly_common_name + '@' + self.modhash_abbrev

    @property
    def tarfile(self):
        return self.cert_name + '.tar.gz'

    @property
    def files(self):
        files = {}
        for content in (self.key, self.csr, self.crt):
            if content:
                ext = tar.get_file_ext(content)
                files[self.cert_name + ext] = content
        return files

    def save(self, tarpath):
        authority = copy.deepcopy(self.authority)
        authority.pop('key', None)
        authority.pop('csr', None)
        authority.pop('crt', None)
        yml = {
            self.cert_name: {
                'common_name': self.common_name,
                'timestamp': self.timestamp,
                'modhash': self.modhash,
                'bug': self.bug,
                'expiry': self.expiry,
                'authority': self.authority,
            }
        }
        if self.sans:
            yml[self.cert_name]['sans'] = self.sans
        return tar.bundle(
            tarpath,
            self.cert_name,
            self.key,
            self.csr,
            self.crt,
            yml,
            self.readme)

    def to_json(self):
        json = {
            self.cert_name: {
                'common_name': self.common_name,
                'timestamp': self.timestamp,
                'modhash': self.modhash,
                'bug': self.bug,
                'expiry': self.expiry,
                'authority': self.authority,
                'destinations': self.destinations,
                'tardata': {
                    self.tarfile: self.files
                },
            }
        }
        if self.sans:
            json[self.cert_name]['sans'] = self.sans
        return json

    def transform(self, verbosity):
        json = self.to_json()
        if verbosity == 0:
            json = {self.cert_name: self.expiry}
        elif verbosity == 1:
            json[self.cert_name].pop('destinations', None)
            json[self.cert_name]['tardata'] = self.tarfile
        elif verbosity == 2:
            json = visit(json, func=simple)
        elif verbosity == 3:
            json = visit(json, func=abbrev)
        return json
