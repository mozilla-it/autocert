#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify
api = Blueprint('list_api', __name__)

from fnmatch import fnmatch
from attrdict import AttrDict

from autocert.config import CFG
from autocert.utils.dictionary import merge

from autocert import digicert

INVALID_STATUS = [
    'expired',
    'rejected',
]

def is_valid_cert(status):
    return status not in INVALID_STATUS

def digicert_list_certs():
    from flask import current_app
    current_app.logger.info('digicert_list_certs called')
    response, ad = digicert.get('order/certificate')
    if ad:
        from pprint import pformat
        certs = [{'{0}.{1}'.format(o.certificate.common_name, o.id): o.certificate} for o in ad.orders if is_valid_cert(o.status)]
        return {
            'certs': certs,
        }
    else:
        app.logger.error('failed request to /list/certs with status_code={0}'.format(response.status_code))

def letsencrypt_list_certs():
    from flask import current_app
    current_app.logger.info('letsencrypt_list_certs called')
    return {
        'certs': []
    }

AUTHORITIES = {
    'digicert': digicert_list_certs,
    'letsencrypt': letsencrypt_list_certs,
}

@api.route('/list/certs', methods=['GET'])
@api.route('/list/certs/<string:pattern>', methods=['GET'])
def list_certs(pattern='*'):
    from flask import current_app
    current_app.logger.info('/list/certs called with pattern="{pattern}"'.format(**locals()))
    authorities = [authority for authority in AUTHORITIES.keys() if fnmatch(authority, pattern)]
    current_app.logger.debug('authorities="{authorities}"'.format(**locals()))
    return jsonify(merge(*[AUTHORITIES[a]() for a in authorities]))
