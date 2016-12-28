#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import zipfile
import requests
from attrdict import AttrDict
from pprint import pformat

from autocert.utils.dictionary import merge
from autocert.certificate import ENCODING

try:
    from autocert.app import app
except ImportError:
    from app import app

try:
    from autocert.config import CFG
except ImportError:
    from config import CFG

class CrtUnzipError(Exception):
    def __init__(self):
        msg = 'failed unzip crt from bytes content'.format(**locals())
        super(CrtUnzipError, self).__init__(msg)

def request(method, path, json=None):
    authority = CFG.authorities.digicert
    url = authority.baseurl / path
    response = requests.request(method, url, auth=authority.auth, json=json)
    try:
        ad = AttrDict(response.json())
    except ValueError:
        ad = None
    return response, ad

def get(path):
    return request('GET', path)

def put(path, json=None):
    return request('PUT', path, json=json)

def post(path, json=None):
    return request('POST', path, json=json)

def suffix(order_id):
    return 'dc{order_id}'.format(**locals())

def unzip_crt(content):
    zf = zipfile.ZipFile(io.BytesIO(content), 'r')
    crts = [fi for fi in zf.infolist() if fi.filename.endswith('.crt')]
    for crt in crts:
        if not crt.filename.endswith('DigiCertCA.crt'):
            return zf.read(crt).decode('utf-8')
    raise CrtUnzipError

def get_crt(common_name):
    pass

def request_certificate(common_name, csr, cert_type='ssl_plus'):
    app.logger.info('called request_certificate:\n{0}'.format(pformat(locals())))
    authority = CFG.authorities.digicert
    path = 'order/certificate/{cert_type}'.format(**locals())
    json = merge(authority.template, {
        'certificate': {
            'common_name': common_name,
            'csr': csr,
        }
    })
    app.logger.debug('calling digicert with path={path} and json={json}'.format(**locals()))
    return post(path, json=json)

def approve_certificate(request_id):
    app.logger.info('called approve_certificate:\n{0}'.format(pformat(locals())))
    path = 'request/{request_id}/status'.format(**locals())
    json = {
        'status': 'approved',
        'processor_comment': 'auto-cert',
    }
    app.logger.debug('calling digicert with path={path} and json={json}'.format(**locals()))
    return put(path, json=json)

def get_certificate_order(order_id):
    app.logger.info('called get_certificate_id:\n{0}'.format(pformat(locals())))
    path = 'order/certificate/{order_id}'.format(**locals())
    return get(path)

def download_certificate(order_id, format_type='pem_all'):
    app.logger.info('called get_certificate:\n{0}'.format(pformat(locals())))
    response, order = get_certificate_order(order_id)
    certificate_id = order.certificate.id
    path = 'certificate/{certificate_id}/download/format/{format_type}'.format(**locals())
    return get(path)
