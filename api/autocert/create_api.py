#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
api for creating certificates
'''

from flask import Blueprint, jsonify, request
api = Blueprint('create_api', __name__)

import json
import requests

from pprint import pformat
from attrdict import AttrDict

from autocert.config import CFG
from autocert.utils.dictionary import merge
from autocert.certificate import (
    call_authority_api,
    create_key,
    create_csr,
    _unzip_digicert_crt,
    ENCODING)

def jsonified_errors(response):
    return jsonify({
        'errors': [
            '{0}: {1}'.format(response.status_code, response.text),
        ],
    })

def request_digicert_certificate(common_name, key, csr, cert_type='ssl_plus'):
    from flask import current_app as app
    authority = CFG.authorities.digicert
    app.logger.info('called request_digicert_certificate:\n{0}'.format(pformat(locals())))
    path = 'order/certificate/{cert_type}'.format(**locals())
    data = json.dumps(merge(authority.template, {
        'certificate': {
            'common_name': common_name,
            'csr': csr.public_bytes(ENCODING[CFG.key.encoding]).decode('utf-8'),
        }
    }))
    app.logger.debug('calling digicert with path={path} and data={data}'.format(**locals()))
    response = call_authority_api(path, authority=authority, method='POST', data=data)
    return response

def approve_digicert_certificate(request_id):
    from flask import current_app as app
    authority = CFG.authorities.digicert
    app.logger.info('called approve_digicert_certificate:\n{0}'.format(pformat(locals())))
    path = 'request/{request_id}/status'.format(**locals())
    data = json.dumps({
        'status': 'approved',
        'processor_comment': 'auto-cert',
    })
    app.logger.debug(
        'calling digicert with path={path} and data={data}'.format(**locals()))
    response = call_authority_api(path, authority=authority, method='PUT', data=data)
    return response

@api.route('/create/digicert/<string:common_name>', methods=['PUT'])
def create(common_name):
    from flask import current_app as app
    data = request.get_json(silent=True)
    sans = data['sans']
    app.logger.info('called /create/digicert:\n{0}'.format(pformat(locals())))
    key = create_key(common_name)
    csr = create_csr(key, common_name, sans)
    request_response = request_digicert_certificate(common_name, key, csr)
    if request_response.status_code != 201:
        return jsonified_errors(request_response)
    request_id = request_response.json()['requests'][0]['id']
    app.logger.debug('request_id={request_id}'.format(**locals()))
    approve_response = approve_digicert_certificate(request_id)
    if approve_response.status_code != 204:
        return jsonified_errors(approve_response)
    return jsonify({
        'messages': [
            '{common_name} cert successfully created'.format(**locals()),
        ],
    })

@api.route('/create/letsencrypt/<string:common_name>', methods=['PUT'])
def create_letsencrypt(common_name):
    from flask import current_app as app
    app.logger.info('called /create/letsencrypt:\n{0}'.format(pformat(locals())))
    raise NotImplementedError('create_letsencrypt endpoint not implemented')
