#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pformat
from attrdict import AttrDict
from flask import make_response, jsonify, request

from autocert.tar import tar_cert_files
from autocert.certificate import create_key_and_csr
from autocert import digicert

try:
    from autocert.app import app
except ImportError:
    from app import app

class UnknownCertificateAuthorityError(Exception):
    def __init__(self, authority):
        msg = 'unknown certificate authority: {0}'.format(authority)
        super(UnknownCertificateAuthorityError, self).__init__(msg)

def defaults(json):
    if not json:
        json = {}
    json['common_name'] = json.get('common_name', '*')
    json['sans'] = json.get('sans', None)
    json['authority'] = json.get('authority', 'digicert')
    return AttrDict(json)

def create_digicert(common_name, sans):
    app.logger.info('called /create/digicert:\n{0}'.format(pformat(locals())))

    messages = []
    key, csr = create_key_and_csr(common_name, sans=sans)

    res1, order = digicert.request_certificate(common_name, csr)
    if res1.status_code != 201:
        return jsonified_errors(res1)
    messages += ['{common_name} cert requested'.format(**locals())]

    res2, _ = digicert.approve_certificate(order.requests[0].id)
    if res2.status_code != 204:
        return jsonified_errors(res2)
    messages += ['{common_name} cert approved'.format(**locals())]

    tarname = common_name + '.' + digicert.suffix(order.id)
    tarpath = tar_cert_files(tarname, key, csr)
    messages += ['saved key and csr to {tarpath}'.format(**locals())]

    records = digicert.get_active_certificate_orders_and_details(common_name)

    return {'certs': records}

def create(json=None):
    args = defaults(json)

    if args.authority == 'digicert':
        results = create_digicert(args.common_name, args.sans)
    elif args.authority == 'letsencrypt':
        results = {'certs': []}
    else:
        raise UnknownCertificateAuthorityError(args.authority)
    return make_response(jsonify(results), 201)

