#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pytest

from subprocess import check_output

from utils.format import fmt, pfmt
from utils.cert import Cert

DIR = os.path.dirname(os.path.realpath(__file__))
KEY = open(DIR+'/key').read()
CSR = open(DIR+'/csr').read()
CRT = open(DIR+'/crt').read()


@pytest.fixture
def cert():
    return Cert(
        'common.name',
        20170209155541 ,
        KEY,
        CSR,
        CRT,
        expiry=20170401000000,
        authority=dict(digicert=dict(order_id=1298368)))

def test_ctor(cert):
    assert isinstance(cert, Cert)

def test_cert_name(cert):
    assert cert.cert_name == '{0}@{1}'.format(cert.common_name, cert.timestamp)

def test_files(cert):
    assert cert.files == {
        cert.cert_name + '.key': KEY,
        cert.cert_name + '.csr': CSR,
        cert.cert_name + '.crt': CRT,
    }

def test_to_disk(cert, tmpdir):
    tarpath = tmpdir.mkdir('tarpath')
    tarfile = cert.to_disk(tarpath)
    output = check_output('tar -tvf ' + tarfile, shell=True).decode('utf-8')
    assert cert.cert_name + '.key' in output

def test_roundtrip(cert, tmpdir, capsys):
    tarpath = tmpdir.mkdir('tarpath')
    tarfile = cert.to_disk(tarpath)
    cert2 = Cert.from_disk(tarpath, cert.cert_name)
    assert cert.common_name == cert2.common_name
    assert cert.timestamp == cert2.timestamp
    assert cert.key == cert2.key
    assert cert.csr == cert2.csr
    assert cert.crt == cert2.crt
    assert cert.expiry == cert2.expiry
    assert cert.authority == cert2.authority
