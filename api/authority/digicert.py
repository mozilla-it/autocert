#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import zipfile
from attrdict import AttrDict
from pprint import pprint, pformat
from fnmatch import fnmatch
from datetime import timedelta #FIXME: do we import this here?

from authority.base import AuthorityBase
from utils.dictionary import merge, body
from utils.format import fmt, pfmt
from cert import create_cert_name

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

def expiryify(valid_till):
    from utils.timestamp import string2int
    if valid_till and valid_till != 'null':
        return string2int(valid_till)
    return valid_till

def certify(common_name, timestamp, expiry, order_id, csr=None, crt=None, cert=None):
    if cert == None:
        cert = {}
    cert_name = create_cert_name(common_name, timestamp)
    digicert = dict(order_id=order_id)
    if csr:
        digicert['csr'] = csr
    if crt:
        digicert['crt'] = crt
    return merge(cert, {
        cert_name: dict(
            common_name=common_name,
            timestamp=timestamp,
            expiry=expiry,
            authority=dict(
                digicert=digicert))})

class DigicertAuthority(AuthorityBase):
    def __init__(self, ar, cfg, verbosity):
        super(DigicertAuthority, self).__init__(ar, cfg, verbosity)

    def display_certificates(self, certs, repeat_delta=None):
        common_names = [body(cert)['common_name'] for cert in certs]
        timestamps = [body(cert)['timestamp'] for cert in certs]
        order_ids = [body(cert)['authority']['digicert']['order_id'] for cert in certs]
        calls = self._get_certificate_order_detail(order_ids)
        certificate_ids = [call.recv.json.certificate.id for call in calls]
        crts = self._download_certificates(certificate_ids, repeat_delta=repeat_delta)
        expiries = [expiryify(call.recv.json.certificate.valid_till) for call in calls]
        csrs = [call.recv.json.certificate.csr for call in calls]
        return [certify(*args) for args in zip(common_names, timestamps, expiries, order_ids, csrs, crts, certs)]

    def create_certificate(self, common_name, timestamp, csr, sans=None, repeat_delta=None):
        app.logger.info(fmt('create_certificate:\n{locals}'))
        path = 'order/certificate/ssl_plus'
        json = merge(self.cfg.template, dict(
            certificate=dict(
                common_name=common_name,
                csr=csr)))
        if sans:
            path = 'order/certificate/ssl_multi_domain'
            json = merge(json, dict(
                certificate=dict(
                    dns_names=sans)))
        order_ids, request_ids = self._order_certificates([path], [json])
        pfmt('order_ids={order_ids}')
        result = self._approve_certificates(request_ids)
        pfmt('result={result}')
        calls = self._get_certificate_order_detail(order_ids)
        certificate_ids = [call.recv.json.certificate.id for call in calls]
        pfmt('certificate_ids={certificate_ids}')
        try:
            crt = self._download_certificates(certificate_ids, repeat_delta=repeat_delta)[0]
            call = self._get_certificate_order_detail(order_ids)[0]
            expiry = expiryify(call.recv.json.certificate.valid_till)
        except DownloadCertificateError as dce:
            crt = None
            expiry = None
        cert = certify(common_name, timestamp, expiry, order_ids[0])
        if sans:
            cert['sans'] = list(sans)
        return crt, cert

    def renew_certificates(self, certs):
        pass

    def revoke_certificates(self, certs):
        raise NotImplementedError

    def _order_certificates(self, paths, jsons):
        app.logger.info(fmt('_order_certificates:\n{locals}'))
        calls = self.posts(paths=paths, jsons=jsons)
        for call in calls:
            if call.recv.status != 201:
                raise OrderCertificateError(call)
        result = zip(*[(call.recv.json.id, call.recv.json.requests[0].id) for call in calls])
        result = list(result)
        pfmt('result={result}')
        return result

    def _approve_certificates(self, request_ids):
        app.logger.info(fmt('_approve_certificates:\n{locals}'))
        paths = [fmt('request/{request_id}/status') for request_id in request_ids]
        jsons = [dict(status='approved', processor_common='autocert')]
        app.logger.debug(fmt('calling digicert api with paths={paths} and jsons={jsons}'))
        calls = self.puts(paths=paths, jsons=jsons)
        for call in calls:
            if call.recv.status != 204:
                raise ApproveCertificateError(call)
        return True

    def _get_certificate_order_detail(self, order_ids):
        app.logger.info(fmt('_get_certificate_order_detail:\n{locals}'))
        paths = [fmt('order/certificate/{order_id}') for order_id in order_ids]
        calls = self.gets(paths=paths)
        return calls

    def _download_certificates(self, certificate_ids, format_type='pem_all', repeat_delta=None):
        app.logger.info(fmt('_download_certificates:\n{locals}'))
        if repeat_delta is not None and isinstance(repeat_delta, int):
            repeat_delta = timedelta(seconds=repeat_delta)
        paths = [fmt('certificate/{certificate_id}/download/format/{format_type}') for certificate_id in certificate_ids]
        calls = self.gets(paths=paths, repeat_delta=repeat_delta, repeat_if=not_200)
        texts = [call.recv.text if call.recv.status == 200 else DownloadCertificateError(call) for call in calls]
        return texts
