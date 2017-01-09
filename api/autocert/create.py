#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pformat
from attrdict import AttrDict
from flask import make_response, jsonify, request

from autocert.tar import tar_cert_files
from autocert.certificate import create_key_and_csr
from autocert import digicert
from autocert import show

try:
    from autocert.app import app
except ImportError:
    from app import app

class UnknownCertificateAuthorityError(Exception):
    def __init__(self, authority):
        msg = 'unknown certificate authority: {0}'.format(authority)
        super(UnknownCertificateAuthorityError, self).__init__(msg)

def create_digicert(common_name, sans, verbosity):
    app.logger.info('called /create/digicert:\n{0}'.format(pformat(locals())))
    key, csr = create_key_and_csr(common_name, sans=sans)
    res1, order = digicert.request_certificate(common_name, csr)
    if res1.status_code != 201:
        return jsonified_errors(res1)
    res2, _ = digicert.approve_certificate(order.requests[0].id)
    if res2.status_code != 204:
        return jsonified_errors(res2)
    cert_name = common_name + '.' + digicert.suffix(order.id)
    cert_path = tar_cert_files(cert_name, key, csr)
    certs = digicert.get_active_certificate_orders_and_details(common_name)
    return {'certs': certs}, 201

def create(common_name, sans, authority, verbosity, **kwargs):
    app.logger.info('create: {0}'.format(locals()))
    if authority == 'digicert':
        json, status_code = create_digicert(common_name, sans, verbosity)
        if status_code == 201:
            json, status_code = show.show(common_name, verbosity)
    elif authority == 'letsencrypt':
        json = {'certs': []}
    else:
        raise UnknownCertificateAuthorityError(authority)
    return json, 201

