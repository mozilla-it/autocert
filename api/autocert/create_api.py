#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
api for creating certificates
'''

from flask import Blueprint, jsonify, request
api = Blueprint('create_api', __name__)

from pprint import pformat

from autocert.tar import tar_cert_files
from autocert.certificate import create_key_and_csr
from autocert import digicert

try:
    from autocert.app import app
except ImportError:
    from app import app

def jsonified_errors(response):
    return jsonify({
        'errors': [
            '{0}: {1}'.format(response.status_code, response.text),
        ],
    })

@api.route('/create/digicert/<string:common_name>', methods=['PUT'])
def create_digicert(common_name):
    data = request.get_json(silent=True)
    sans = data['sans']
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

    return jsonify({
        'messages': messages,
        'order_id': order.id,
        'request_id': order.requests[0].id,
    })

@api.route('/create/letsencrypt/<string:common_name>', methods=['PUT'])
def create_letsencrypt(common_name):
    app.logger.info('called /create/letsencrypt:\n{0}'.format(pformat(locals())))
    raise NotImplementedError('create_letsencrypt endpoint not implemented')
