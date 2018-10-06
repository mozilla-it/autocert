#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import copy
import glob
import time
import tarfile

from io import BytesIO
from ruamel import yaml
from datetime import datetime, timedelta

from exceptions import AutocertError
from utils.dictionary import merge, head, body, head_body, keys_ending
from utils.yaml import yaml_format
from utils.isinstance import *
from utils import timestamp
from utils import pki
from utils.fmt import *
from config import CFG

FILETYPE = {
    '-----BEGIN RSA PRIVATE KEY-----':          '.key',
    '-----BEGIN CERTIFICATE REQUEST-----':      '.csr',
    '-----BEGIN NEW CERTIFICATE REQUEST-----':  '.csr',
    '-----BEGIN CERTIFICATE-----':              '.crt',
}

class UnknownFileExtError(AutocertError):
    def __init__(self, content):
        message = fmt('unknown filetype for this content: {content}')
        super(UnknownFileExtError, self).__init__(message)

class BundleFromJsonError(AutocertError):
    def __init__(self, ex):
        message = 'cert.from_json error'
        super(BundleFromJsonError, self).__init__(message)
        self.errors = [ex]

class BundleLoadError(AutocertError):
    def __init__(self, tarpath, cert_name, ex):
        message = fmt('error loading {cert_name}.tar.gz from {tarpath}')
        super(BundleLoadError, self).__init__(message)
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

def get_file_ext(content):
    for head, ext in FILETYPE.items():
        if content.startswith(head):
            return ext
    return '.yml'

def tarinfo(name, content):
    ext = get_file_ext(content) if name != 'README' else ''
    info = tarfile.TarInfo(name + ext)
    info.mtime = time.time()
    info.size = len(content)
    return info

class BundleProperties(type):
    '''
    Bundle properties
    properties on classmethods https://stackoverflow.com/a/47334224
    '''

    ZERO = timedelta(0)

    TIMESTAMP = timestamp.utcnow()

    BUNDLE_PATH = str(CFG.bundle.path)

    README = open(os.path.dirname(os.path.abspath(__file__)) + '/README.tarfile').read()

    @property
    def files(cls):
        return glob.glob(cls.BUNDLE_PATH + '/*.tar.gz')

    @property
    def names(cls):
        def get_bundle_name(bundle_file):
            ext = '.tar.gz'
            if bundle_file.startswith(cls.BUNDLE_PATH) and bundle_file.endswith(ext):
                return os.path.basename(bundle_file)[0:-len(ext)]
        return [get_bundle_name(bundle_file) for bundle_file in cls.files]

    @property
    def bundles(cls, bundle_name_pns, within=None, expired=False):
        bundles = []
        if isint(within):
            within = timedelta(within)
        for bundle_name in sorted(sift.fnmatches(cls.names, bundle_name_pns)):
            bundle = Bundle.from_disk(bundle_name, bundle_path=cls.bundle_path)
            if bundle.sans:
                bundle.sans = sorted(bundle.sans)
            if within:
                delta = bundle.expiry - cls.TIMESTAMP
                if cls.ZERO < delta and delta < within:
                    bundles += [bundle]
                elif expired:
                    if bundle.expiry < cls.TIMESTAMP:
                        bundle += [bundle]
                else:
                    if bundle.expiry > cls.TIMESTAMP:
                        bundle += [bundle]
        return bundles

class Bundle(object, metaclass=BundleProperties):
    '''
    Bundle class
    '''

    def __init__(self, common_name, timestamp, modhash, key, csr, crt, bug, sans=None, expiry=None, authority=None, destinations=None):
        if authority:
            assert isinstance(authority, dict)
        self.common_name        = common_name
        self.timestamp          = timestamp
        self.modhash            = modhash
        self.key                = key
        self.csr                = csr
        self.crt                = crt
        self.bug                = bug
        self.sans               = sans
        self.expiry             = expiry
        self.authority          = authority
        self.destinations       = destinations if destinations else {}

    def __repr__(self):
        return yaml_format(self.to_obj())

    def __eq__(self, bundle):
        return (
            self.common_name    == bundle.common_name and
            self.timestamp      == bundle.timestamp and
            self.modhash        == bundle.modhash and
            self.key            == bundle.key and
            self.csr            == bundle.csr and
            self.crt            == bundle.crt and
            self.bug            == bundle.bug and
            self.sans           == bundle.sans and
            self.expiry         == bundle.expiry and
            self.authority      == bundle.authority and
            self.destinations   == bundle.destinations)

    @property
    def modhash_abbrev(self):
        return self.modhash[:8]

    @property
    def friendly_common_name(self):
        if self.common_name.startswith('*.'):
            return 'wildcard' + self.common_name[1:]
        return self.common_name

    @property
    def bundle_name(self):
        return self.friendly_common_name + '@' + self.modhash_abbrev

    @property
    def bundle_tar(self):
        return self.bundle_name + '.tar.gz'

    @property
    def serial(self):
        return pki.get_serial(self.crt)

    @property
    def sha1(self):
        return pki.get_sha1(self.crt)

    @property
    def sha2(self):
        return pki.get_sha2(self.crt)

    @property
    def files(self):
        files = {}
        for content in (self.key, self.csr, self.crt):
            if content:
                ext = get_file_ext(content)
                files[self.bundle_name + ext] = content
        return files

    def to_obj(self):
        obj = {
            self.bundle_name: {
                'common_name': self.common_name,
                'timestamp': self.timestamp,
                'modhash': self.modhash,
                'serial': self.serial,
                'sha1': self.sha1,
                'sha2': self.sha2,
                'bug': self.bug,
                'expiry': self.expiry,
                'authority': self.authority,
                'destinations': self.destinations,
                'tardata': {
                    self.bundle_name: self.files
                },
            }
        }
        if self.sans:
            obj[self.bundle_name]['sans'] = self.sans
        return obj

    def to_disk(self, bundle_path=None):
        if bundle_path == None:
            bundle_path = Bundle.BUNDLE_PATH
        authority = copy.deepcopy(self.authority)
        authority.pop('key', None)
        authority.pop('csr', None)
        authority.pop('crt', None)
        obj = {
            self.bundle_name: {
                'common_name': self.common_name,
                'timestamp': self.timestamp,
                'modhash': self.modhash,
                'bug': self.bug,
                'expiry': self.expiry,
                'authority': self.authority,
            }
        }
        if self.sans:
            obj[self.bundle_name]['sans'] = self.sans
        yml = yaml_format(obj)
        os.makedirs(Bundle.BUNDLE_PATH, exist_ok=True)
        bundle_file = fmt('{bundle_path}/{1}.tar.gz', self.bundle_name)
        with tarfile.open(bundle_path, 'w:gz') as tar:
            tar.addfile(tarinfo('README', Bundle.README), BytesIO(Bundle.README.encode('utf-8')))
            for content in (key, csr, crt, yml):
                if content:
                    tar.addfile(tarinfo(bundle_name, content), BytesIO(content.encode('utf-8')))
        return bundle_file

    @staticmethod
    def from_obj(obj):
        try:
            bundle_name, bundle_body = head_body(obj)
            common_name = bundle_body['common_name']
            timestamp = bundle_body['timestamp']
            modhash = bundle_body['modhash']
            expiry = bundle_body['expiry']
            authority = bundle_body['authority']
            bug = bundle_body.get('bug', None)
            sans = bundle_body.get('sans', None)
            destinations = bundle_body.get('destinations', None)
            key, csr, crt = [None] * 3
            tardata = bundle_body.pop('tardata', None)
            if tardata:
                files = tardata[bundle_name + '.tar.gz']
                key = files[bundle_name + '.key']
                csr = files[bundle_name + '.csr']
                crt = files[bundle_name + '.crt']
        except  Exception as ex:
            print(ex)
            raise BundleFromJsonError(ex)
        return common_name, timestamp, modhash, key, csr, crt, bug, sans, expiry, authority, destinations

    @classmethod
    def from_disk(cls, bundle_name, bundle_path=None):
        if bundle_path == None:
            bundle_path = Bundle.BUNDLE_PATH
        bundle_file = fmt('{bundle_path}/{bundle_name}.tar.gz')
        key, csr, crt, obj, readme = [None] * 5
        with tarfile.open(bundle_file, 'r:gz') as tar:
            for info in tar.getmembers():
                info.mtime = time.time()
                if info.name.endswith('.key'):
                    key = tar.extractfile(info.name).read().decode('utf-8')
                elif info.name.endswith('.csr'):
                    csr = tar.extractfile(info.name).read().decode('utf-8')
                elif info.name.endswith('.crt'):
                    crt = tar.extractfile(info.name).read().decode('utf-8')
                elif info.name.endswith('.yml'):
                    yml = tar.extractfile(info.name).read().decode('utf-8')
                    obj = yaml.safe_load(yml)
                elif info.name == 'README':
                    readme = tar.extractfile(info.name).read().decode('utf-8')
        dbg(key)
        try:
            common_name, timestamp, modhash, _, _, _, bug, sans, expiry, authority, destinations = Bundle.from_obj(obj)
        except AutocertError as ae:
            raise BundleLoadError(bundle_path, bundle_name, ae)
        bundle = Bundle(
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
        return bundle

