#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BytesIO
from pprint import pformat
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes, serialization

import tarfile

try:
    from autocert.app import app
except ImportError:
    from app import app

try:
    from autocert.config import CFG
except ImportError:
    from config import CFG

class KeyExistError(Exception):
    def __init__(self, keyfile):
        msg = 'key file {keyfile} does not exist'.format(**locals())
        super(KeyExistError, self).__init__(msg)

class CsrExistError(Exception):
    def __init__(self, csrfile):
        msg = 'csr file {csrfile} does not exist'.format(**locals())
        super(CsrExistError, self).__init__(msg)

OIDS_MAP = {
    'common_name':              NameOID.COMMON_NAME,
    'org_name':                 NameOID.ORGANIZATION_NAME,
    'org_unit':                 NameOID.ORGANIZATIONAL_UNIT_NAME,
    'org_country':              NameOID.COUNTRY_NAME,
    'org_city':                 NameOID.LOCALITY_NAME,
    'org_state':                NameOID.STATE_OR_PROVINCE_NAME,
    'org_zip':                  NameOID.POSTAL_CODE,
    'org_addr1':                NameOID.STREET_ADDRESS,
    'org_addr2':                NameOID.STREET_ADDRESS,
    'org_contact_job_title':    NameOID.TITLE,
    'org_contact_firstname':    NameOID.GIVEN_NAME,
    'org_contact_lastname':     NameOID.SURNAME,
    'org_contact_email':        NameOID.EMAIL_ADDRESS,
}

ENCODING = {
    'DER': serialization.Encoding.DER,
    'PEM': serialization.Encoding.PEM,
}

def _create_key(common_name, **kwargs):
    app.logger.info('called create_key:\n{0}'.format(pformat(locals())))
    key = rsa.generate_private_key(
        public_exponent=kwargs.get('public_exponent', CFG.key.public_exponent),
        key_size=kwargs.get('key_size', CFG.key.key_size),
        backend=default_backend())
    return key

def _create_oids(common_name, oids):
    attrs = [x509.NameAttribute(NameOID.COMMON_NAME, common_name)]
    for key in CFG.csr.oids:
        oid = OIDS_MAP.get(key, None)
        if oid:
            if key in oids:
                value = str(oids[key])
            else:
                value = str(CFG.csr.oids[key])
            attrs += [x509.NameAttribute(oid, value)]
    return attrs

def _add_sans(subject, sans):
    subject.add_extension(
        [x509.DNSName(dns_name) for dns_name in dns_names],
        critical=False)

def _create_csr(common_name, key, oids=None, sans=None):
    app.logger.info('called create_csr:\n{0}'.format(pformat(locals())))
    builder = x509.CertificateSigningRequestBuilder()
    oids = _create_oids(common_name, oids if oids else {})
    subject = builder.subject_name(x509.Name(oids))
    if sans:
        _add_sans(subject, sans)
    csr = subject.sign(key, hashes.SHA256(), default_backend())
    return csr

def create_key_and_csr(common_name, oids=None, sans=None):
    key = _create_key(common_name)
    csr = _create_csr(common_name, key)
    key_text = key.private_bytes(
        encoding=ENCODING[CFG.key.encoding],
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()).decode('utf-8')
    csr_text = csr.public_bytes(ENCODING[CFG.csr.encoding]).decode('utf-8')
    return key_text, csr_text

def key_tarinfo(common_name, key):
    info = tarfile.TarInfo(common_name+'.key')
    info.size = len(key)
    return info

def csr_tarinfo(common_name, csr):
    info = tarfile.TarInfo(common_name+'.csr')
    info.size = len(csr)
    return info

def tar_key_and_csr(common_name, suffix, key, csr, metadata=None):
    filename = str(CFG.tar.dirpath / '{common_name}.{suffix}.tar.gz'.format(**locals()))
    with tarfile.open(filename, 'w:gz') as tar:
        tar.addfile(key_tarinfo(common_name, key), BytesIO(key.encode('utf-8')))
        tar.addfile(csr_tarinfo(common_name, csr), BytesIO(csr.encode('utf-8')))
    return filename

def untar_key_and_csr(common_name, suffix):
    filename = str(CFG.tar.dirpath / '{common_name}.{suffix}.tar.gz'.format(**locals()))
    with tarfile.open(filename, 'r:gz') as tar:
        key = tar.extractfile('{common_name}.key'.format(**locals())).read().decode('utf-8')
        csr = tar.extractfile('{common_name}.csr'.format(**locals())).read().decode('utf-8')
    return key, csr
