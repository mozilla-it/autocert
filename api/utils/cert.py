#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
utils.cert
'''

import copy

from utils import tar
from utils.format import fmt, pfmt
from utils.isinstance import *

from utils.output import yaml_format, output
from utils.dictionary import head, body, head_body, keys_ending
from utils.exceptions import AutocertError


class CertFromJsonError(AutocertError):
    def __init__(self, ex):
        message = 'cert.from_json error'
        super(CertFromJsonError, self).__init__(message)
        self.errors = [ex]

class Cert(object):

    def __init__(self, common_name, timestamp, modhash, key, csr, crt, sans=None, expiry=None, authority=None, destinations=None):
        if authority:
            assert isinstance(authority, dict)
        self.common_name    = common_name
        self.timestamp      = timestamp
        self.modhash        = modhash
        self.key            = key
        self.csr            = csr
        self.crt            = crt
        self.sans           = sans
        self.expiry         = expiry
        self.authority      = authority
        self.destinations   = destinations if destinations else {}

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
            from pprint import pprint
            pprint(cert)
            raise CertFromJsonError(ke)
        return common_name, timestamp, modhash, key, csr, crt, sans, expiry, authority, destinations

    @staticmethod
    def load(tarpath, cert_name):
        key, csr, crt, yml = tar.unbundle(tarpath, cert_name)
        common_name, timestamp, modhash, _, _, _, sans, expiry, authority, destinations = Cert._decompose(yml)
        return Cert(
            common_name,
            timestamp,
            modhash,
            key,
            csr,
            crt,
            sans,
            expiry,
            authority,
            destinations)

    @staticmethod
    def from_json(json):
        common_name, timestamp, modhash, key, csr, crt, sans, expiry, authority, destinations = Cert._decompose(json, True)
        return Cert(
            common_name,
            timestamp,
            modhash,
            key,
            csr,
            crt,
            sans,
            expiry,
            authority,
            destinations)

    @property
    def cert_name(self):
        return '{0}@{1}'.format(self.common_name, self.timestamp)

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
                'sans': self.sans,
                'expiry': self.expiry,
                'authority': self.authority,
            }
        }
        return tar.bundle(
            tarpath,
            self.cert_name,
            self.key,
            self.csr,
            self.crt,
            yml)

    def to_json(self):
        return {
            self.cert_name: {
                'common_name': self.common_name,
                'timestamp': self.timestamp,
                'modhash': self.modhash,
                'sans': self.sans,
                'expiry': self.expiry,
                'authority': self.authority,
                'destinations': self.destinations,
                'tardata': {
                    self.tarfile: self.files
                },
            }
        }
