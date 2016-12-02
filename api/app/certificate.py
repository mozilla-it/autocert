#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

APACHE_SERVER_TYPE = 2

RFC_5280_RENAME = {
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
    with open(str(keyfile), 'rb') as f:
        data = f.read()
    return serialization.load_pem_private_key(data, None, default_backend())

def create_oids(common_name, **oids):
    oids = [x509.NameAttribute(NameOID.COMMON_NAME, common_name)]
    for key, value in CFG.




def create_csr(private_key, common_name, *dns_names):
    csrfile = CFG.key.dirpath / '{common_name}.csr'.format(**locals())
    builder = x509.CertificateSigningRequestBuilder()
    oids = [
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        x509.NameAttribute(NameOID.COUNTRY_NAME, u'US'),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u'CA'),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u'Mountain View'),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u'Mozilla'),
    ]
    subject = builder.subject_name(x509.Name(oids))
    if dns_names:
        subject.add_extension(
            [x509.DNSName(dns_name) for dns_name in dns_names],
            critical=False)
    csr = subject.sign(private_key, hashes.SHA256(), default_backend())
    return csr

