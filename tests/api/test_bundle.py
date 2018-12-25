#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pytest

from subprocess import check_output

from utils import timestamp
from bundle import Bundle

DIR = os.path.dirname(os.path.realpath(__file__))
KEY = open(DIR+'/key').read()
CSR = open(DIR+'/csr').read()
CRT = open(DIR+'/crt').read()

EXPIRY = timestamp.utcnow()
TIMESTAMP = timestamp.utcnow()

@pytest.fixture
def bundle():
    return Bundle(
        'common.name',
        'e8a7fcfbe48df21daede665d78984dec',
        KEY,
        CSR,
        CRT,
        '0000000',
        expiry=EXPIRY,
        authority=dict(digicert=dict(order_id=1298368)),
        timestamp=TIMESTAMP)

@pytest.fixture
def wildcard_bundle():
    return Bundle(
        '*.common.name',
        'e8a7fcfbe48df21daede665d78984dec',
        KEY,
        CSR,
        CRT,
        '0000000',
        expiry=EXPIRY,
        authority=dict(digicert=dict(order_id=1298368)),
        timestamp=TIMESTAMP)

def test_ctor(bundle):
    assert isinstance(bundle, Bundle)

def test_modhash_abbrev(bundle):
    assert bundle.modhash_abbrev == bundle.modhash[:8]

def test_bundle_name(bundle):
    assert bundle.bundle_name == '{0}@{1}'.format(bundle.common_name, bundle.modhash_abbrev)

def test_wildcard_bundle_name(wildcard_bundle):
    assert wildcard_bundle.bundle_name == 'wildcard.common.name@e8a7fcfb'

def test_bundle_tar(bundle):
    assert bundle.bundle_tar == bundle.bundle_name + '.tar.gz'

def test_files(bundle):
    assert bundle.files == {
        bundle.bundle_name + '.key': KEY,
        bundle.bundle_name + '.csr': CSR,
        bundle.bundle_name + '.crt': CRT,
    }

def test_disk_roundtrip(bundle, tmpdir, capsys):
    bundle_path = str(tmpdir.mkdir('bundle_path'))
    bundle_file = bundle.to_disk(bundle_path=bundle_path)
    bundle2 = Bundle.from_disk(bundle.bundle_name, bundle_path=bundle_path)
    assert bundle == bundle2

def test_json_roundtrip(bundle):
    json = bundle.to_obj()
    common_name, modhash, key, csr, crt, bug, sans, expiry, authority, destinations, timestamp = Bundle.from_obj(json)
    bundle2 = Bundle(
        common_name,
        modhash,
        key,
        csr,
        crt,
        bug,
        sans=sans,
        expiry=expiry,
        authority=authority,
        destinations=destinations,
        timestamp=timestamp)
    assert bundle == bundle2
