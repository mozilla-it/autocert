#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
utils.cert
'''

import copy

from pprint import pprint

from utils import tar
from utils.format import fmt, pfmt
from utils.isinstance import *

from utils.output import yaml_format, output
from utils.dictionary import head, body, head_body, keys_ending


class Cert(object):

    def __init__(self, common_name, timestamp, key, csr, crt, expiry=None, authority=None, destinations=None): #FIXME: from CFG?
        self.common_name    = common_name
        self.timestamp      = timestamp
        self.key            = key
        self.csr            = csr
        self.crt            = crt
        self.expiry         = expiry
        self.authority      = authority
        self.destinations   = destinations

    def __repr__(self):
        return yaml_format(self.to_json())

    def __eq__(self, cert):
        return (
            self.common_name == cert.common_name and
            self.timestamp == cert.timestamp and
            self.key == cert.key and
            self.csr == cert.csr and
            self.crt == cert.crt and
            self.expiry == cert.epiry and
            self.authority == cert.authority) #and
            #self.destinations == cert.destinations)

    @staticmethod
    def from_disk(tarpath, cert_name):
        key, csr, crt, yml = tar.unbundle(tarpath, cert_name)
        return Cert(
            yml.pop('common_name', None),
            yml.pop('timestamp', None),
            key,
            csr,
            crt,
            expiry=yml.pop('expiry', None),
            authority=yml)

    @staticmethod
    def from_json(json):
        pass

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

    def to_disk(self, tarpath):
        print('to_disk:')
        yml = copy.deepcopy(self.authority)
        print('yml')
        pprint(yml)
        yml.pop('key', None)
        yml.pop('csr', None)
        yml.pop('crt', None)
        yml.update(dict(
            common_name=self.common_name,
            timestamp=self.timestamp,
            expiry=self.expiry))
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
                'expiry': self.expiry,
                'destinations': self.destinations,
                'authority': self.authority,
                'tardata': {
                    self.tarfile: self.files
                },
            }
        }
