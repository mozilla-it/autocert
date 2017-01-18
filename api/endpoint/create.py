#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pformat
from attrdict import AttrDict
from flask import make_response, jsonify, request
from datetime import timedelta

from utils.tar import tar_cert_files
from utils.format import fmt

from endpoint.base import EndpointBase

try:
    from autocert.app import app
except ImportError:
    from app import app

class UnknownCertificateAuthorityError(Exception):
    def __init__(self, authority):
        msg = fmt('unknown certificate authority: {authority}')
        super(UnknownCertificateAuthorityError, self).__init__(msg)

class CreateEndpoint(EndpointBase):
    def __init__(self, cfg, verbosity):
        super(CreateEndpoint, self).__init__(cfg, verbosity)

    def execute(self, **kwargs):
        key, csr = create_key_csr(self.common_name, self.sans)
        crt, yml = self.authority.create_certificate(
            self.common_name,
            csr,
            self.sans,
            self.repeat_delta)
        self.cert_name = create_cert_name(self.common_name)
        tar_cert_files(cert_name, key, csr, crt, yml)
        status = 201
        return self.json(cert_name, status)

    def respond(self, **kwargs):
        return {
            'certs': [],
            'calls': [],
        }

#def create_digicert(common_name, sans, verbosity):
#    app.logger.info('called /create/digicert:\n{0}'.format(pformat(locals())))
#    key, csr = create_key_and_csr(common_name, sans=sans)
#    res1, order = digicert.request_certificate(common_name, csr)
#    if res1.status_code != 201:
#        return jsonified_errors(res1)
#    res2, _ = digicert.approve_certificate(order.requests[0].id)
#    if res2.status_code != 204:
#        return jsonified_errors(res2)
#    cert_name = common_name + '.' + digicert.suffix(order.id)
#    cert_path = tar_cert_files(cert_name, key, csr)
#    certs = digicert.get_active_certificate_orders_and_details(common_name)
#    return {'certs': certs}, 201

#def create(common_name, sans, authority, verbosity, **kwargs):
#    app.logger.info('create: {0}'.format(locals()))
#    if authority == 'digicert':
#        json, status_code = create_digicert(common_name, sans, verbosity)
#        if status_code == 201:
#            json, status_code = show.show(common_name, verbosity)
#    elif authority == 'letsencrypt':
#        json = {'certs': []}
#    else:
#        raise UnknownCertificateAuthorityError(authority)
#    return json, 201





