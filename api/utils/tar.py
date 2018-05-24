
import os
import glob
import tarfile

from io import BytesIO
from ruamel import yaml

from utils.format import fmt
from utils.yaml import yaml_format
from utils.dictionary import merge
from utils.exceptions import AutocertError

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

def bundle(dirpath, cert_name, key, csr, crt, yml, readme):
    os.makedirs(str(dirpath), exist_ok=True)
    if not yml:
        yml = {}
    yml = yaml_format(yml)
    tarpath = fmt('{dirpath}/{cert_name}.tar.gz')
    with tarfile.open(tarpath, 'w:gz') as tar:
        readme_info = tarfile.TarInfo('README')
        readme_info.size = len(readme)
        tar.addfile(readme_info, BytesIO(readme.encode('utf-8')))
        for content in (key, csr, crt, yml):
            if content:
                tar.addfile(tarinfo(cert_name, content), BytesIO(content.encode('utf-8')))
    return tarpath

def unbundle(dirpath, cert_name):
    key, csr, crt, yml, readme = [None] * 5
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
                yml = yaml.safe_load(yml)
            elif info.name == 'README':
                readme = tar.extractfile(info.name).read().decode('utf-8')
    return key, csr, crt, yml, readme
