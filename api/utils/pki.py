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

import tarfile

from config import CFG
from utils.format import fmt
from utils.exceptions import AutocertError

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

KEY_LOAD_FUNC = dict(
    DER = serialization.load_der_private_key,
    PEM = serialization.load_pem_private_key,
)

CSR_LOAD_FUNC = dict(
    DER = x509.load_der_x509_csr,
    PEM = x509.load_pem_x509_csr,
)

CRT_LOAD_FUNC = dict(
    DER = x509.load_der_x509_certificate,
    PEM = x509.load_pem_x509_certificate,
)

def _keyobj_to_keystr(keyobj):
    return keyobj.private_bytes(
        encoding=ENCODING[CFG.key.encoding],
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()).decode('utf-8')

def _keystr_to_keyobj(keystr):
    return KEY_LOAD_FUNC[CFG.key.encoding](
        keystr.encode('utf-8'),
        password=None,
        backend=default_backend())

def _csrobj_to_csrstr(csrobj):
    return csrobj.public_bytes(ENCODING[CFG.csr.encoding]).decode('utf-8')

def _csrstr_to_csrobj(csrstr):
    return CSR_LOAD_FUNC[CFG.csr.encoding](
        csrstr.encode('utf-8'),
        backend=default_backend())

def _create_keyobj(common_name, public_exponent=None, key_size=None):
    return rsa.generate_private_key(
        public_exponent=public_exponent if public_exponent else CFG.key.public_exponent,
        key_size=key_size if key_size else CFG.key.key_size,
        backend=default_backend())

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
        x509.SubjectAlternativeName([x509.DNSName(san) for san in sans]),
        critical=False)

def _create_csrobj(common_name, keyobj, oids=None, sans=None):
    builder = x509.CertificateSigningRequestBuilder()
    oids = _create_oids(common_name, oids if oids else {})
    subject = builder.subject_name(x509.Name(oids))
    if sans:
        _add_sans(subject, sans)
    csr = subject.sign(keyobj, hashes.SHA256(), default_backend())
    return csr

def create_key(common_name, public_exponent=None, key_size=None):
    keyobj = _create_keyobj(common_name, public_exponent=None, key_size=None)
    return _keyobj_to_keystr(keyobj)

def create_csr(common_name, key, oids=None, sans=None):
    keyobj = _keystr_to_keyobj(key) if isinstance(key, str) else key
    csrobj = _create_csrobj(common_name, keyobj, oids, sans)
    return _csrobj_to_csrstr(csrobj)

def create_modhash(key):
    keyobj = _keystr_to_keyobj(key) if isinstance(key, str) else key
    modulus_int = keyobj.private_numbers().public_numbers.n
    modulus_hex = hex(modulus_int).rstrip('L').lstrip('0x').upper()
    modulus_bytes = fmt('Modulus={modulus_hex}\n').encode('utf-8')
    md5 = hashlib.md5()
    md5.update(modulus_bytes)
    return md5.hexdigest()

def create_modhash_key_and_csr(common_name, oids=None, sans=None):
    key = create_key(common_name)
    csr = create_csr(common_name, key, oids, sans)
    modhash = create_modhash(key)
    return (modhash, key, csr)
