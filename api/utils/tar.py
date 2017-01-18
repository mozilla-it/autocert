#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import tarfile

from io import BytesIO
from ruamel import yaml

from utils.format import fmt
from utils.output import yaml_format
from utils.dictionary import merge

from app import app

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
    return '.yml'

def tarinfo(cert_name, content):
    ext = get_file_ext(content)
    info = tarfile.TarInfo(cert_name + ext)
    info.size = len(content)
    return info

def tar_cert_files(cert_name, key, csr, crt, yml):
    if not yml:
        yml = {}
    yml = yaml_format(yml)
    tarpath = str(CFG.tar.dirpath / cert_name) + '.tar.gz'
    with tarfile.open(tarpath, 'w:gz') as tar:
        for content in (key, csr, crt, yml):
            if content:
                tar.addfile(tarinfo(cert_name, content), BytesIO(content.encode('utf-8')))
    return tarpath

def untar_cert_files(cert_name):
    key, csr, crt, yml = [None] * 4
    tarpath = str(CFG.tar.dirpath / cert_name) + '.tar.gz'
    with tarfile.open(tarpath, 'r:gz') as tar:
        for info in tar.getmembers():
            if info.name.endswith('.key'):
                key = tar.extractfile(info.name).read().decode('utf-8')
            elif info.name.endswith('.csr'):
                csr = tar.extractfile(info.name).read().decode('utf-8')
            elif info.name.endswith('.crt'):
                crt = tar.extractfile(info.name).read().decode('utf-8')
            elif info.name.endswith('.yml'):
                yml = tar.extractfile(info.name).read().decode('utf-8')
                yml = {cert_name: yaml.safe_load(yml)}
    return key, csr, crt, yml

def get_cert_from_tarfile(cert_name, dirpath=CFG.tar.dirpath):
    key, csr, crt, yml = untar_cert_files(cert_name)
    if not yml:
        yml = {cert_name: {}}

    files = {}
    for content in (key, csr, crt):
        if content:
            ext = get_file_ext(content)
            files[fmt('{cert_name}{ext}')] = content

    cert = {
        cert_name: {
            'tarfile': {
                fmt('{dirpath}/{cert_name}.tar.gz'): files
            }
        }
    }
    return merge(cert, yml)

def get_certs_from_tarfiles(cert_name_pattern='*', dirpath=CFG.tar.dirpath):
    certs = []
    for cert_path in glob.glob(fmt('{dirpath}/{cert_name_pattern}.tar.gz')):
        cert_name = os.path.basename(cert_path).replace('.tar.gz', '')
        certs += [get_cert_from_tarfile(cert_name)]
    return certs
