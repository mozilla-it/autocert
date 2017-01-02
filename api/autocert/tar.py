#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import tarfile

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

def tarinfo(tarname, content):
    ext = get_file_ext(content)
    info = tarfile.TarInfo(tarname + ext)
    info.size = len(content)
    return info

def tar_cert_files(tarname, key, csr, crt=None):
    tarpath = str(CFG.tar.dirpath / tarname) + '.tar.gz'
    with tarfile.open(tarpath, 'w:gz') as tar:
        for content in (key, csr, crt):
            if content:
                tar.addfile(tarinfo(tarname, content), BytesIO(content.encode('utf-8')))
    return tarpath

def untar_cert_files(tarname):
    tarpath = str(CFG.tar.dirpath / tarname) + '.tar.gz'
    with tarfile.open(tarpath, 'r:gz') as tar:
        key = tar.extractfile('{tarname}.key'.format(**locals())).read().decode('utf-8')
        csr = tar.extractfile('{tarname}.csr'.format(**locals())).read().decode('utf-8')
        try:
            crt = tar.extractfile('{tarname}.crt'.format(**locals())).read().decode('utf-8')
        except KeyError:
            crt = None
    return key, csr, crt

def get_records_from_tarfiles(common_name_pattern='*', dirpath=CFG.tar.dirpath):
    records = {}
    for tarpath in glob.glob('{dirpath}/{common_name_pattern}.tar.gz'.format(**locals())):
        tarname = os.path.basename(tarpath).replace('.tar.gz', '')
        key, csr, crt = untar_cert_files(tarname)
        records[tarname] = {
            'tarfile': {
                tarpath: {
                    tarname + '.key': key,
                    tarname + '.csr': csr,
                }
            }
        }
    return records
