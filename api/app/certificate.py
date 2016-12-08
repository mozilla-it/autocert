#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import zipfile
import requests

from functools import partial

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes, serialization

try:
    from app.config import CFG
except ImportError as ie:
    from config import CFG

class KeyExistError(Exception):
    def __init__(self, keyfile):
        msg = 'key file {keyfile} does not exist'.format(**locals())
        super(KeyExistError, self).__init__(msg)

class CsrExistError(Exception):
    def __init__(self, csrfile):
        msg = 'csr file {csrfile} does not exist'.format(**locals())
        super(CsrExistError, self).__init__(msg)

class CrtUnzipError(Exception):
    def __init__(self):
        msg = 'failed unzip crt from bytes content'.format(**locals())
        super(CrtUnzipError, self).__init__(msg)

APACHE_SERVER_TYPE = 2

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

STATUS_CODES = {
    200: [True,     ''],
    201: [True,     'Created'],
    204: [True,     'No content'],
    400: [False,    'General client error'],
    401: [False,    'Invalid account ID and API key combination'],
    403: [False,    'API key missing permissions required'],
    404: [False,    'Page does not exist'],
    405: [False,    'Method not found'],
    406: [False,    'Requested content type or API version is invalid'],
}

def create_key(common_name, **kwargs):
    keyfile = CFG.key.dirpath / '{common_name}.key'.format(**locals())
    key = rsa.generate_private_key(
        public_exponent=kwargs.get('public_exponent', CFG.key.public_exponent),
        key_size=kwargs.get('key_size', CFG.key.key_size),
        backend=default_backend())
    with open(str(keyfile), 'wb') as f:
        f.write(key.private_bytes(
            encoding=ENCODING[CFG.key.encoding],
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()))
    return key

def load_key(common_name):
    keyfile = CFG.key.dirpath / '{common_name}.key'.format(**locals())
    if not keyfile.exists():
        raise KeyExistError(csrfile)
    with open(str(keyfile), 'rb') as f:
        data = f.read()
    return serialization.load_pem_private_key(data, None, default_backend())

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
    if sans:
        subject.add_extension(
            [x509.DNSName(dns_name) for dns_name in dns_names],
            critical=False)

def create_csr(key, common_name, oids=None, sans=None):
    if not oids:
        oids = {}
    if not sans:
        sans = []
    csrfile = CFG.key.dirpath / '{common_name}.csr'.format(**locals())
    builder = x509.CertificateSigningRequestBuilder()
    oids = create_oids(common_name, oids)
    subject = builder.subject_name(x509.Name(oids))
    add_sans(subject, sans)
    csr = subject.sign(key, hashes.SHA256(), default_backend())
    with open(str(csrfile), 'wb') as f:
        f.write(csr.public_bytes(ENCODING[CFG.csr.encoding]))
    return csr

def load_csr(common_name):
    csrfile = CFG.key.dirpath / '{common_name}.csr'.format(**locals())
    if not csrfile.exists():
        raise CsrExistError(csrfile)
    with open(str(csrfile), 'rb') as f:
        csr = x509.lead_pem_x509_csr(r.read(), default_backend())
    return csr

def _unzip_digicert_crt(content):
    zf = zipfile.ZipFile(io.BytesIO(content), 'r')
    crts = [fi for fi in zf.infolist() if fi.filename.endswith('.crt')]
    for crt in crts:
        if not crt.filename.endswith('DigiCertCA.crt'):
            return zf.read(crt).decode('utf-8')
    raise CrtUnzipError

def call_provider_api(path, provider=CFG.providers.digicert, method='GET', headers=None, data=None):
    if not headers:
        headers = {
            'Content-Type': 'application/json',
        }

    url = provider.baseurl / path
    return requests.request(method, url, auth=provider.auth, headers=headers, data=data)

