#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from functools import partial
from OpenSSL import crypto
from OpenSSL.crypto import(
    FILETYPE_PEM as PEM,
    TYPE_RSA as RSA)
from OpenSSL._util import (
    ffi,
    lib,
    exception_from_error_queue)

class OpenSSLCryptoError(Exception):
    """
    An error occurred in an `OpenSSL.crypto` API.
    """

RFC_5280_RENAME = {
    'common_name':  'commonName',
    'org_city':     'localityName',
    'org_country':  'countryName',
    'org_unit':     'organizationalUnitName',
    'org_name':     'organizationName',
    'org_state':    'stateOrProvinceName'
}

def dict_to_attrs(obj, d):
    for k, v in d.items():
        setattr(obj, k, v)
    return obj

def create_pkey(pkey_type, pkey_bits):
    pkey = crypto.PKey()
    pkey.generate_key(pkey_type, pkey_bits)
    return pkey

def create_request(attrs):
    request = crypto.X509Req()
    subject = request.get_subject()
    for k, v in attrs.items():
        setattr(subject, RFC_5280_RENAME.get(k, k), v)
    return request

def update(d1, d2):
    d1.update(d2)
    return d1

def dump_rsa_private_key(pkey, file_type=PEM):
    # Based off of https://github.com/pyca/pyopenssl/blob/27398343217703c5261e67d6c19dda89ba559f1b/OpenSSL/crypto.py#L1418-L1466

    raise_current_error = partial(exception_from_error_queue, OpenSSLCryptoError)

    bio = crypto._new_mem_buf()

    cipher_obj = ffi.NULL

    rsa = lib.EVP_PKEY_get1_RSA(pkey._pkey)
    helper = crypto._PassphraseHelper(file_type, None)
    result_code = lib.PEM_write_bio_RSAPrivateKey(
        bio, rsa, cipher_obj, ffi.NULL, 0,
        helper.callback, helper.callback_args)
    helper.raise_if_problem()

    if result_code == 0:
        raise_current_error()

    return crypto._bio_to_string(bio)

def generate_csr(pkey_type=RSA, pkey_bits=2048, digest_type='md5', file_type=PEM, **attrs):
    pkey = create_pkey(pkey_type, pkey_bits)
    request = create_request(attrs)
    request.set_pubkey(pkey)
    request.sign(pkey, digest_type)
    return update(attrs, {
        'private_key': dump_rsa_private_key(pkey, file_type),
        'csr': crypto.dump_certificate_request(file_type, request),
    })
