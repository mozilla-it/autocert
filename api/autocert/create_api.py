#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
api for creating certificates
'''

from flask import Blueprint, jsonify, request
api = Blueprint('create_api', __name__)

from pprint import pformat

from autocert.certificate import create_key, create_csr
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
    key = create_key(common_name)
    csr = create_csr(key, common_name, sans)
    res1, ad1 = digicert.request_certificate(common_name, key, csr)
    if res1.status_code != 201:
        return jsonified_errors(res1)
    request_id = ad1.requests[0].id
    res2, ad2 = digicert.approve_certificate(request_id)
    if res2.status_code != 204:
        return jsonified_errors(res2)
    return jsonify({
        'messages': [
            '{common_name} cert successfully created'.format(**locals()),
        ],
    })

@api.route('/create/letsencrypt/<string:common_name>', methods=['PUT'])
def create_letsencrypt(common_name):
    app.logger.info('called /create/letsencrypt:\n{0}'.format(pformat(locals())))
    raise NotImplementedError('create_letsencrypt endpoint not implemented')
