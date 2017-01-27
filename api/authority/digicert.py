#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import zipfile
from attrdict import AttrDict
from pprint import pprint, pformat
from fnmatch import fnmatch
from datetime import timedelta #FIXME: do we import this here?

from authority.base import AuthorityBase
from utils.dictionary import merge
from utils.format import fmt, pfmt
from utils.timestamp import string2int

from app import app

def not_200(call):
    return call.recv.status != 200

class OrderCertificateError(Exception):
    def __init__(self, call):
        msg = fmt('order certificate error call={0}', call)
        super(OrderCertificateError, self).__init__(msg)

class ApproveCertificateError(Exception):
    def __init__(self, call):
        msg = fmt('approve certificate error call={0}', call)
        super(ApproveCertificateError, self).__init__(msg)

class DownloadCertificateError(Exception):
    def __init__(self, call):
        msg = fmt('download certificate error call={0}', call)
        super(DownloadCertificateError, self).__init__(msg)

class DigicertAuthority(AuthorityBase):
    def __init__(self, ar, cfg, verbosity):
        super(DigicertAuthority, self).__init__(ar, cfg, verbosity)

    def display(self, cert_name):
        raise NotImplementedError

    def create_certificate(self, common_name, timestamp, csr, sans=None, repeat_delta=None):
        app.logger.info(fmt('create_certificate:\n{locals}'))
        order_id, request_id = self._order_certificate(common_name, csr, sans)
        self._approve_certificate(request_id)
        call = self._get_certificate_order_detail(order_id)
        try:
            crt = self._download_certificate(call.recv.json.certificate.id, repeat_delta=repeat_delta)
            call = self._get_certificate_order_detail(order_id)
            expires = call.recv.json.certificate.valid_till
            if expires and expires != 'null':
                expires = string2int(expires)
        except DownloadCertificateError as dce:
            crt = None
            expires = None
        yml = dict(
            common_name=common_name,
            timestamp=timestamp,
            authority=dict(
                digicert=dict(
                    order_id=order_id,
                    expires=expires)))
        if sans:
            yml['sans'] = list(sans)
        return crt, yml

    def renew_certificate(self, cert_name):
        raise NotImplementedError

    def revoke_certificate(self, cert_name):
        raise NotImplementedError

    def _cert_name(self, common_name, order_id):
        return fmt('{common_name}.dc{order_id}')

    def _order_certificate(self, common_name, csr, sans=None):
        app.logger.info(fmt('_order_certificate:\n{locals}'))
        path = 'order/certificate/ssl_plus'
        json = merge(self.cfg.template, {
            'certificate': {
                'common_name': common_name,
                'csr': csr,
            }
        })
        if sans:
            path = 'order/certificate/ssl_multi_domain'
            json = merge(json, {
                'certificate': {
                    'dns_names': sans
                }
            })
        app.logger.debug(fmt('calling digicert api with path={path} and json={json}'))
        call = self.post(path=path, json=json)
        if call.recv.status == 201:
            return call.recv.json.id, call.recv.json.requests[0].id
        raise OrderCertificateError(call)

    def _approve_certificate(self, request_id):
        app.logger.info(fmt('_approve_certificate:\n{locals}'))
        path = fmt('request/{request_id}/status')
        json = {
            'status': 'approved',
            'processor_comment': 'auto-cert',
        }
        app.logger.debug(fmt('calling digicert api with path={path} and json={json}'))
        call = self.put(path=path, json=json)
        if call.recv.status == 204:
            return True
        raise ApproveCertificateError(call)

    def _get_certificate_order_detail(self, order_id):
        app.logger.info(fmt('_get_certificate_order_detail:\n{locals}'))
        path = fmt('order/certificate/{order_id}')
        return self.get(path=path)

    def _download_certificate(self, certificate_id, format_type='pem_all', repeat_delta=None):
        app.logger.info(fmt('_download_certificate:\n{locals}'))
        if repeat_delta is not None and isinstance(repeat_delta, int):
            repeat_delta = timedelta(seconds=repeat_delta)

        path = fmt('certificate/{certificate_id}/download/format/{format_type}')
        call = self.get(path=path, repeat_delta=repeat_delta, repeat_if=not_200)
        if call.recv.status == 200:
            return call.recv.text
        raise DownloadCertificateError(call)








