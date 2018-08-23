#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import hashlib
from pprint import pformat
from datetime import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes, serialization

from exceptions import AutocertError
from utils.fmt import *
from config import CFG
from app import app
import tarfile

class KeyExistError(AutocertError):
    def __init__(self, keyfile):
        message = 'key file {keyfile} does not exist'.format(**locals())
        super(KeyExistError, self).__init__(message)

class CsrExistError(AutocertError):
    def __init__(self, csrfile):
        message = 'csr file {csrfile} does not exist'.format(**locals())
        super(CsrExistError, self).__init__(message)

class CertNameDecomposeError(AutocertError):
    def __init__(self, pattern, cert_name):
        message = '"{cert_name}" could not be decomposed with pattern "{pattern}"'.format(**locals())
        super(CertNameDecomposeError, self).__init__(message)

OIDS_MAP = dict(
    common_name =              NameOID.COMMON_NAME,
    org_name =                 NameOID.ORGANIZATION_NAME,
    org_unit =                 NameOID.ORGANIZATIONAL_UNIT_NAME,
    org_country =              NameOID.COUNTRY_NAME,
    org_city =                 NameOID.LOCALITY_NAME,
    org_state =                NameOID.STATE_OR_PROVINCE_NAME,
    org_zip =                  NameOID.POSTAL_CODE,
    org_addr1 =                NameOID.STREET_ADDRESS,
    org_addr2 =                NameOID.STREET_ADDRESS,
    org_contact_job_title =    NameOID.TITLE,
    org_contact_firstname =    NameOID.GIVEN_NAME,
    org_contact_lastname =     NameOID.SURNAME,
    org_contact_email =        NameOID.EMAIL_ADDRESS,
)

ENCODING = dict(
    DER = serialization.Encoding.DER,
    PEM = serialization.Encoding.PEM,
)

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

def _create_modhash(key):
    modulus_int = key.private_numbers().public_numbers.n
    modulus_hex = hex(modulus_int).rstrip('L').lstrip('0x').upper()
    modulus_bytes = fmt('Modulus={modulus_hex}\n').encode('utf-8')
    md5 = hashlib.md5()
    md5.update(modulus_bytes)
    return md5.hexdigest()

def create_modhash_key_and_csr(common_name, oids=None, sans=None):
    key = _create_key(common_name)
    csr = _create_csr(common_name, key)
    modhash = _create_modhash(key)
    return (
        modhash,
        key.private_bytes(
            encoding=ENCODING[CFG.key.encoding],
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()).decode('utf-8'),
        csr.public_bytes(ENCODING[CFG.csr.encoding]).decode('utf-8'))
