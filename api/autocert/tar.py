#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import tarfile

from io import BytesIO

try:
    from autocert.app import app
except ImportError:
    from app import app

try:
    from autocert.config import CFG
except ImportError:
    from config import CFG

FILETYPE = {
    '-----BEGIN RSA PRIVATE KEY-----':      '.key',
    '-----BEGIN CERTIFICATE REQUEST-----':  '.csr',
    '-----BEGIN CERTIFICATE-----':          '.crt',
}

class UnknownFileExtError(Exception):
    def __init__(self, content):
        msg = 'unknown filetype for this content: {0}'.format(content)
        super(UnknownFileExtError, self).__init__(msg)

def get_file_ext(content):
    for head, ext in FILETYPE.items():
        if content.startswith(head):
            return ext
    raise UnknownFileExtError(content)

def tarinfo(cert_name, content):
    ext = get_file_ext(content)
    info = tarfile.TarInfo(cert_name + ext)
    info.size = len(content)
    return info

def tar_cert_files(cert_name, key, csr, crt=None):
    tarpath = str(CFG.tar.dirpath / cert_name) + '.tar.gz'
    with tarfile.open(tarpath, 'w:gz') as tar:
        for content in (key, csr, crt):
            if content:
                tar.addfile(tarinfo(cert_name, content), BytesIO(content.encode('utf-8')))
    return tarpath

def untar_cert_files(cert_name):
    tarpath = str(CFG.tar.dirpath / cert_name) + '.tar.gz'
    with tarfile.open(tarpath, 'r:gz') as tar:
        key = tar.extractfile('{cert_name}.key'.format(**locals())).read().decode('utf-8')
        csr = tar.extractfile('{cert_name}.csr'.format(**locals())).read().decode('utf-8')
        try:
            crt = tar.extractfile('{cert_name}.crt'.format(**locals())).read().decode('utf-8')
        except KeyError:
            crt = None
    return key, csr, crt

def get_record_from_tarfile(cert_name, dirpath=CFG.tar.dirpath):
    key, csr, crt = untar_cert_files(cert_name)
    return {
        'tarfile': {
            cert_name + '.key': key,
            cert_name + '.csr': csr,
        }
    }

def get_records_from_tarfiles(cert_name_pattern='*', dirpath=CFG.tar.dirpath):
    records = {}
    for cert_path in glob.glob('{dirpath}/{cert_name_pattern}.tar.gz'.format(**locals())):
        cert_name = os.path.basename(cert_path).replace('.tar.gz', '')
        records[cert_name] = get_record_from_tarfile(cert_name)
    return records
