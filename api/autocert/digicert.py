#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import zipfile
import requests
from attrdict import AttrDict
from pprint import pprint, pformat
from fnmatch import fnmatch

from autocert.utils.newline import windows2unix
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

INVALID_STATUS = [
    'expired',
    'rejected',
]

class CrtUnzipError(Exception):
    def __init__(self):
        msg = 'failed unzip crt from bytes content'.format(**locals())
        super(CrtUnzipError, self).__init__(msg)

class DigicertGetOrderDetailError(Exception):
    def __init__(self, response):
        msg = '{response}'.format(**locals())
        super(DigicertGetOrderDetailError, self).__init__(msg)

class DigicertDownloadCertificateError(Exception):
    def __init__(self, response):
        msg = 'response.status_code = {0} response.text = {1}'.format(response.status_code, response.text)
        super(DigicertDownloadCertificateError, self).__init__(msg)

def request(method, path, json=None, attrdict=True):
    authority = CFG.authorities.digicert
    url = authority.baseurl / path
    response = requests.request(method, url, auth=authority.auth, json=json)
    try:
        obj = response.json()
        if attrdict:
            obj = AttrDict(obj)
    except ValueError:
        obj = None
    return response, obj

def get(path, attrdict=True):
    return request('GET', path, attrdict=attrdict)

def put(path, json=None, attrdict=True):
    return request('PUT', path, json=json, attrdict=attrdict)

def post(path, json=None, attrdict=True):
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

def get_certificate_orders():
    app.logger.info('get_certficate_orders')
    r, o = get('order/certificate', attrdict=False)
    return o['orders']

def filter_common_name(orders, common_name):
    return [order for order in orders if fnmatch(order['certificate']['common_name'], common_name)]

def filter_active_status(orders):
    return [order for order in orders if order['status'] not in INVALID_STATUS]

def get_valid_certificate_orders(common_name='*'):
    app.logger.info('get_valid_certificate_orders: common_name={0}'.format(common_name))
    orders = get_certificate_orders()
    orders = filter_active_status(orders)
    orders = filter_common_name(orders, common_name)
    return orders

def get_order_detail(order_id):
    r, detail = get('order/certificate/{order_id}'.format(**locals()), attrdict=False)
    if r.status_code == 200:
        return detail
    raise DigicertGetOrderDetailError(r)

def get_csr(detail):
    return detail.certificate.csr

def create_record(order):
    common_name = order.certificate.common_name
    record_name = '{0}.{1}'.format(common_name, suffix(order.id))
    expires = order.certificate.valid_till
    crt = download_certificate(order.id)
    detail = get_order_detail(order.id)
    csr = get_csr(AttrDict(detail))
    return {
        '{record_name}'.format(**locals()): {
            'common_name': common_name,
            'suffix': suffix(order.id),
            'expires': expires,
            'authorities': {
                'digicert': {
                    'csr': csr,
                    'crt': crt,
                    'data': {
                        'order': dict(order),
                        'detail': detail,
                    }
                }
            }
        }
    }

def get_active_certificate_orders_and_details(common_name='*'):
    orders = get_valid_certificate_orders(common_name)
    records = []
    for order in orders:
        records += [create_record(AttrDict(order))]
    return records

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
    r, _ = get(path)
    if r.status_code == 200:
        return windows2unix(r.text)
    elif r.status_code == 404 and 'certificate has not yet been issued' in r.text:
        return r.json()['errors'][0]['message']
    raise DigicertDownloadCertificateError(r)
