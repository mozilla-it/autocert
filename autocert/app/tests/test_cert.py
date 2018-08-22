#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import pytest

from subprocess import check_output

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(DIR, '../')))

from utils.fmt import *
from cert import Cert

KEY = open(DIR+'/key').read()
CSR = open(DIR+'/csr').read()
CRT = open(DIR+'/crt').read()

@pytest.fixture
def cert():
    return Cert(
        'common.name',
        20170209155541,
        'e8a7fcfbe48df21daede665d78984dec',
        KEY,
        CSR,
        CRT,
        '0000000',
        expiry=20170401000000,
        authority=dict(digicert=dict(order_id=1298368)))

@pytest.fixture
def wildcard_cert():
    return Cert(
        '*.common.name',
        20170209155541,
        'e8a7fcfbe48df21daede665d78984dec',
        KEY,
        CSR,
        CRT,
        '0000000',
        expiry=20170401000000,
        authority=dict(digicert=dict(order_id=1298368)))

def test_ctor(cert):
    assert isinstance(cert, Cert)

def test_modhash_abbrev(cert):
    assert cert.modhash_abbrev == cert.modhash[:8]

def test_cert_name(cert):
    assert cert.cert_name == '{0}@{1}'.format(cert.common_name, cert.modhash_abbrev)

def test_wildcard_cert_name(wildcard_cert):
    assert wildcard_cert.cert_name == 'wildcard.common.name@e8a7fcfb'

def test_tarfile(cert):
    assert cert.tarfile == cert.cert_name + '.tar.gz'

def test_files(cert):
    assert cert.files == {
        cert.cert_name + '.key': KEY,
        cert.cert_name + '.csr': CSR,
        cert.cert_name + '.crt': CRT,
    }

def test_disk_roundtrip(cert, tmpdir, capsys):
    tarpath = tmpdir.mkdir('tarpath')
    tarfile = cert.save(tarpath)
    cert2 = Cert.load(tarpath, cert.cert_name)
    assert cert == cert2

def test_json_roundtrip(cert):
    json = cert.to_json()
    cert2 = Cert.from_json(json)
    assert cert == cert2
