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

    @staticmethod
    def from_disk(tarpath):
        pass

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

    def __repr__(self):
        return yaml_format(self.to_json())

    def to_disk(self, tarpath):
        yml = copy.deepcopy(self.authority)
        yml.pop('key', None)
        yml.pop('csr', None)
        yml.pop('crt', None)
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
