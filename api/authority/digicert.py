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

class OrganizationNameNotFoundError(Exception):
    def __init__(self, organization_name):
        msg = fmt('organization name {organization_name} not found')
        super(OrganizationNameNotFoundError, self).__init__(msg)

class NotValidatedDomainError(Exception):
    def __init__(self, common_name):
        msg = fmt('domain not validated for {common_name}')
        super(NotValidatedDomainError, self).__init__(msg)

def expiryify(valid_till):
    from utils.timestamp import string2int
    if valid_till and valid_till != 'null':
        return string2int(valid_till)
    return valid_till

#def certify(common_name, timestamp, expiry, order_id, csr=None, crt=None, cert=None):
#    if cert == None:
#        cert = {}
#    cert_name = create_cert_name(common_name, timestamp)
#    digicert = dict(order_id=order_id)
#    if csr:
#        digicert['csr'] = csr
#    if crt:
#        digicert['crt'] = crt
#    return merge(cert, {
#        cert_name: dict(
#            common_name=common_name,
#            timestamp=timestamp,
#            expiry=expiry,
#            authority=dict(
#                digicert=digicert))})

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

    def create_certificate(self, organization_name, common_name, timestamp, csr, sans=None, repeat_delta=None):
        app.logger.info(fmt('create_certificate:\n{locals}'))
        organization_id, container_id = self._get_organization_container_ids(organization_name)
        if not self._is_validated_domain(common_name, organization_id, container_id):
            raise NotValidatedDomainError(common_name)
        path, json = self._prepare_path_json(organization_id, common_name, csr, sans=sans)
        crts, expiries, order_ids = self._create_certificates([path], [json], repeat_delta)
        cert = certify(common_name, timestamp, expiries[0], order_ids[0])
        if sans:
            cert['sans'] = list(sans)
        return crts[0], cert

    def renew_certificates(self, certs):
        paths = []
        jsons = []
        for cert in certs:
            path, json = self._cert_to_path_json(cert)
            paths += path
            jsons += json
        crts, expiries, order_ids = self._create_certificates(paths, jsons, repeat_delta)
        raise NotImplementedError

    def revoke_certificates(self, certs):
        raise NotImplementedError

    def _get_organization_container_ids(self, organization_name):
        path = 'organization'
        call = self.get(path)
        for organization in call.recv.json.organizations:
            if organization.name == organization_name:
                return organization.id, organization.container.id
        raise OrganizationNameNotFoundError(organization_name)

    def _get_domains(self, organization_id, container_id):
        call = self.get(fmt('domain?container_id={container_id}'))
        return [domain for domain in call.recv.json.domains if domain.organization.id == organization_id]

    def _is_validated_domain(self, common_name, organization_id, container_id):
        app.logger.info(fmt('_is_validated_domain:\n{locals}'))
        domains = self._get_domains(organization_id, container_id)
        matched_domains = [domain for domain in domains if common_name == domain.name]
        if matched_domains:
            domain = matched_domains[0]
        else:
            matched_subdomains = [domain for domain in domains if common_name.endswith('.'+domain.name)]
            if matched_subdomains:
                domain = matched_subdomains[0]
            else:
                return False
        return domain.is_active

    def _prepare_path_json(self, organization_id, common_name, csr, sans=None):
        path = 'order/certificate/ssl_plus'
        json = merge(self.cfg.template, dict(
            certificate=dict(
                common_name=common_name,
                csr=csr),
            organization=dict(
                id=organization_id)))
        if sans:
            path = 'order/certificate/ssl_multi_domain'
            json = merge(json, dict(
                certificate=dict(
                    dns_names=sans)))
        return path, json

    def _cert_to_path_json(self, cert):
        cert_body = body(cert)
        timestamp = cert_body['timestamp']
        common_name = cert_body['common_name']
        sans = cert_body.get('sans', None)
        order_id = cert_body['autority']['digicert']['order_id']
        tar_body = body(cert_body['tardata'])
        csr = tar_body[fmt('{common_name}@{timestamp}.csr')]
        path, json = self._prepare_path_json(common_name, csr, sans=sans)
        json['renewal_of_order_id'] = order_id
        return path, json

    def _create_certificates(self, paths, jsons, repeat_delta):
        order_ids, request_ids = self._order_certificates(paths, jsons)
        self._approve_certificates(request_ids)
        calls = self._get_certificate_order_detail(order_ids)
        certificate_ids = [call.recv.json.certificate.id for call in calls]
        try:
            crts = self._download_certificates(certificate_ids, repeat_delta=repeat_delta)
            calls = self._get_certificate_order_detail(order_ids)
            expiries = [expiryify(call.recv.json.certificate.valid_till) for call in calls]
        except DownloadCertificateError as dce:
            app.logger.warning(str(dce))
            crt = None
            expiry = None
        return crts, expiries, order_ids

    def _order_certificates(self, paths, jsons):
        app.logger.info(fmt('_order_certificates:\n{locals}'))
        calls = self.posts(paths=paths, jsons=jsons)
        for call in calls:
            if call.recv.status != 201:
                raise OrderCertificateError(call)
        return zip(*[(call.recv.json.id, call.recv.json.requests[0].id) for call in calls])

    def _approve_certificates(self, request_ids):
        app.logger.info(fmt('_approve_certificates:\n{locals}'))
        paths = [fmt('request/{request_id}/status') for request_id in request_ids]
        jsons = [dict(status='approved', processor_common='autocert')]
        app.logger.debug(fmt('calling digicert api with paths={paths} and jsons={jsons}'))
        calls = self.puts(paths=paths, jsons=jsons)
        for call in calls:
            if call.recv.status != 204:
                if call.recv.json.errors[0].code != 'request_already_processed':
                    raise ApproveCertificateError(call)
        return True

    def _get_certificate_order_detail(self, order_ids):
        app.logger.info(fmt('_get_certificate_order_detail:\n{locals}'))
        paths = [fmt('order/certificate/{order_id}') for order_id in order_ids]
        calls = self.gets(paths=paths)
        return calls

    def _download_certificates(self, certificate_ids, format_type='pem_noroot', repeat_delta=None):
        app.logger.info(fmt('_download_certificates:\n{locals}'))
        if repeat_delta is not None and isinstance(repeat_delta, int):
            repeat_delta = timedelta(seconds=repeat_delta)
        paths = [fmt('certificate/{certificate_id}/download/format/{format_type}') for certificate_id in certificate_ids]
        calls = self.gets(paths=paths, repeat_delta=repeat_delta, repeat_if=not_200)
        texts = [call.recv.text if call.recv.status == 200 else DownloadCertificateError(call) for call in calls]
        return texts
