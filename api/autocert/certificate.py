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

def create_key(common_name, **kwargs):
    app.logger.info('called create_key:\n{0}'.format(pformat(locals())))
    keyfile = CFG.key.dirpath / '{common_name}.key'.format(**locals())
    key = rsa.generate_private_key(
        public_exponent=kwargs.get('public_exponent', CFG.key.public_exponent),
        key_size=kwargs.get('key_size', CFG.key.key_size),
        backend=default_backend())
    return key

def create_oids(common_name, oids):
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

def add_sans(subject, sans):
    subject.add_extension(
        [x509.DNSName(dns_name) for dns_name in dns_names],
        critical=False)

def create_csr(key, common_name, oids=None, sans=None):
    app.logger.info('called create_csr:\n{0}'.format(pformat(locals())))
    csrfile = CFG.key.dirpath / '{common_name}.csr'.format(**locals())
    builder = x509.CertificateSigningRequestBuilder()
    oids = create_oids(common_name, oids if oids else {})
    subject = builder.subject_name(x509.Name(oids))
    if sans:
        add_sans(subject, sans)
    csr = subject.sign(key, hashes.SHA256(), default_backend())
    return csr

def key_info_and_bytes(common_name, key):
    key_bytes = BytesIO(key.private_bytes(
        encoding=ENCODING[CFG.key.encoding],
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()))
    key_info = tarfile.TarInfo(common_name+'.key')
    key_info.size = key_bytes.getbuffer().nbytes
    return key_info, key_bytes

def csr_info_and_bytes(common_name, csr):
    csr_bytes = BytesIO(csr.public_bytes(ENCODING[CFG.csr.encoding]))
    csr_info = tarfile.TarInfo(common_name+'.csr')
    csr_info.size = csr_bytes.getbuffer().nbytes
    return csr_info, csr_bytes

def create_tar(common_name, suffix, key, csr, metadata=None):
    filename = CFG.tar.dirpath / '{common_name}.{suffix}.tar.gz'.format(**locals())
    with tarfile.open(str(filename), 'w:gz') as tar:
        key_info, key_bytes = key_info_and_bytes(common_name, key)
        tar.addfile(key_info, fileobj=key_bytes)
        csr_info, csr_bytes = csr_info_and_bytes(common_name, csr)
        tar.addfile(csr_info, csr_bytes)
    return filename

def load_key_and_csr(filename):
    pass
