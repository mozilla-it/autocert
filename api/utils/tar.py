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

FILETYPE = {
    '-----BEGIN RSA PRIVATE KEY-----':      '.key',
    '-----BEGIN CERTIFICATE REQUEST-----':  '.csr',
    '-----BEGIN CERTIFICATE-----':          '.crt',
}

class UnknownFileExtError(Exception):
    def __init__(self, content):
        msg = fmt('unknown filetype for this content: {content}')
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

def bundle(dirpath, cert_name, key, csr, crt, yml):
    if not yml:
        yml = {}
    yml = yaml_format(yml)
    tarpath = fmt('{dirpath}/{cert_name}.tar.gz')
    with tarfile.open(tarpath, 'w:gz') as tar:
        for content in (key, csr, crt, yml):
            if content:
                tar.addfile(tarinfo(cert_name, content), BytesIO(content.encode('utf-8')))
    return tarpath

def unbundle(dirpath, cert_name):
    key, csr, crt, yml = [None] * 4
    tarpath = fmt('{dirpath}/{cert_name}.tar.gz')
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
