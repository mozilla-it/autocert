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
from utils.newline import windows2unix
from utils.exceptions import AutocertError

from app import app

def not_200(call):
    return call.recv.status != 200

class OrderCertificateError(AutocertError):
    def __init__(self, call):
        message = fmt('order certificate error call={0}', call)
        super(OrderCertificateError, self).__init__(message)

class RevokeCertificateError(AutocertError):
    def __init__(self, call):
        message = fmt('revoke certificate error call={0}', call)
        super(RevokeCertificateError, self).__init__(message)

class ApproveCertificateError(AutocertError):
    def __init__(self, call):
        message = fmt('approve certificate error call={0}', call)
        super(ApproveCertificateError, self).__init__(message)

class DownloadCertificateError(AutocertError):
    def __init__(self, call):
        message = fmt('download certificate error call={0}', call)
        super(DownloadCertificateError, self).__init__(message)

class OrganizationNameNotFoundError(AutocertError):
    def __init__(self, organization_name):
        message = fmt('organization name {organization_name} not found')
        super(OrganizationNameNotFoundError, self).__init__(message)

class NotValidatedDomainError(AutocertError):
    def __init__(self, domains):
        domains = ', '.join(domains)
        message = fmt('list of domains NOT validated: {domains}')
        super(NotValidatedDomainError, self).__init__(message)

class DigicertError(AutocertError):
    def __init__(self, call):
        message = 'digicert error without errors field'
        if 'errors' in call.recv.json:
            message = call.recv.json['errors'][0]['message']
        super(DigicertError, self).__init__(message)


def expiryify(call):
    from utils.timestamp import string2datetime
    if call.recv.status != 200:
        raise DigicertError(call)
    try:
        valid_till = call.recv.json.certificate.valid_till
        if valid_till and valid_till != 'null':
            return string2datetime(valid_till)
    except AttributeError as ae:
        raise DigicertError(call)

def combine_sans(sans1, sans2):
    if sans1 is None:
        return list(sans2)
    elif sans2 is None:
        return list(sans1)
    return list(set(list(sans1) + list(sans2)))

class DigicertAuthority(AuthorityBase):
    def __init__(self, ar, cfg, verbosity):
        super(DigicertAuthority, self).__init__(ar, cfg, verbosity)

    def has_connectivity(self):
        call = self.get('user/me')
        if call.recv.status != 200:
            raise AuthorityConnectivityError(call)
        return True

    def display_certificates(self, certs, repeat_delta=None):
        app.logger.info(fmt('display_certificates:\n{locals}'))
        order_ids = [cert.authority['digicert']['order_id'] for cert in certs]
        calls = self._get_certificate_order_detail(order_ids)
        certificate_ids = [call.recv.json.certificate.id for call in calls]
        crts = self._download_certificates(certificate_ids, repeat_delta=repeat_delta)
        expiries = [expiryify(call) for call in calls]
        csrs = [windows2unix(call.recv.json.certificate.csr) for call in calls]
        for expiry, csr, crt, cert in zip(expiries, csrs, crts, certs):
            matched = csr.strip() == cert.csr.strip() and crt.strip() == cert.crt.strip()
            cert.authority['digicert']['matched'] = matched
        return certs

    def create_certificate(self, organization_name, common_name, validity_years, csr, bug, sans=None, repeat_delta=None):
        app.logger.info(fmt('create_certificate:\n{locals}'))
        if not sans:
            sans = []
        organization_id, container_id = self._get_organization_container_ids(organization_name)
        path, json = self._prepare_path_json(
            organization_id,
            container_id,
            common_name,
            validity_years,
            csr,
            bug,
            sans=sans)
        crts, expiries, order_ids = self._create_certificates([path], [json], bug, repeat_delta)
        authority = dict(digicert=dict(order_id=order_ids[0]))
        return crts[0], expiries[0], authority

    def renew_certificates(self, certs, organization_name, validity_years, bug, sans=None, repeat_delta=None):
        app.logger.info(fmt('renew_certificates:\n{locals}'))
        if not sans:
            sans = []
        organization_id, container_id = self._get_organization_container_ids(organization_name)
        paths, jsons = self._prepare_paths_jsons_for_renewals(
            certs,
            organization_id,
            container_id,
            bug,
            validity_years,
            sans)
        crts, expiries, order_ids = self._create_certificates(paths, jsons, bug, repeat_delta)
        authorities = [dict(digicert=dict(order_id=order_id)) for order_id in order_ids]
        return crts, expiries, authorities

    def revoke_certificates(self, certs, bug):
        app.logger.info(fmt('revoke_certificates:\n{locals}'))
        paths, jsons = self._prepare_paths_jsons_for_revocations(certs, bug)
        self._revoke_certificates(paths, jsons, bug)
        return certs

    def _get_organization_container_ids(self, organization_name):
        app.logger.debug(fmt('_get_organization_container_ids:\n{locals}'))
        path = 'organization'
        call = self.get(path)
        if call.recv.status != 200:
            raise DigicertError(call)
        for organization in call.recv.json.organizations:
            if organization.name == organization_name:
                return organization.id, organization.container.id
        raise OrganizationNameNotFoundError(organization_name)

    def _get_domains(self, organization_id, container_id):
        app.logger.debug(fmt('_get_domains:\n{locals}'))
        call = self.get(fmt('domain?container_id={container_id}'))
        if call.recv.status != 200:
            raise DigicertError(call)
        return [domain for domain in call.recv.json.domains if domain.is_active and domain.organization.id == organization_id]

    def _validate_domains(self, organization_id, container_id, domains):
        app.logger.debug(fmt('_validate_domains:\n{locals}'))
        active_domains = self._get_domains(organization_id, container_id)
        def _is_validated(domain_to_check):
            matched_domains = [ad for ad in active_domains if domain_to_check == ad.name]
            if matched_domains:
                domain = matched_domains[0]
            else:
                matched_subdomains = [ad for ad in active_domains if domain_to_check.endswith('.'+ad.name)]
                if matched_subdomains:
                    domain = matched_subdomains[0]
                else:
                    return False
            return True
        denied_domains = [domain for domain in domains if not _is_validated(domain)]
        if denied_domains:
            raise NotValidatedDomainError(denied_domains)
        return True

    def _prepare_path_json(self, organization_id, container_id, common_name, validity_years, csr, bug, sans=None, renewal_of_order_id=None):
        app.logger.debug(fmt('_prepare_path_json:\n{locals}'))
        domains_to_check = [common_name] + sans if sans else []
        self._validate_domains(organization_id, container_id, domains_to_check)
        path = 'order/certificate/ssl_plus'
        json = merge(self.cfg.template, dict(
            validity_years=validity_years,
            certificate=dict(
                common_name=common_name,
                csr=csr),
            organization=dict(
                id=organization_id),
            comments=bug))
        if common_name.startswith('*.'):
            path = 'order/certificate/ssl_wildcard'
        elif sans:
            path = 'order/certificate/ssl_multi_domain'
            json = merge(json, dict(
                certificate=dict(
                    dns_names=sans)))
        if renewal_of_order_id:
            json = merge(json, dict(
                renewal_of_order_id=renewal_of_order_id))
        return path, json

    def _prepare_paths_jsons_for_renewals(self, certs, organization_id, container_id, bug, validity_years, sans_to_add):
        app.logger.debug(fmt('_prepare_paths_jsons_for_renewals:\n{locals}'))
        order_ids = [cert.authority['digicert']['order_id'] for cert in certs]
        calls = self._get_certificate_order_detail(order_ids)
        paths = []
        jsons = []
        for cert, call in zip(certs, calls):
            cert.sans=combine_sans(cert.sans, sans_to_add)
            path, json = self._prepare_path_json(
                organization_id,
                container_id,
                cert.common_name,
                validity_years,
                cert.csr,
                bug,
                sans=cert.sans,
                renewal_of_order_id=cert.authority['digicert']['order_id'])
            paths += [path]
            jsons += [json]
        return paths, jsons

    def _prepare_paths_jsons_for_revocations(self, certs, bug):
        app.logger.debug(fmt('_prepare_paths_jsons_for_revocations:\n{locals}'))
        order_ids = [cert.authority['digicert']['order_id'] for cert in certs]
        calls = self._get_certificate_order_detail(order_ids)
        certificate_ids = [call.recv.json.certificate.id for call in calls]
        paths = [fmt('certificate/{certificate_id}/revoke') for certificate_id in certificate_ids]
        jsons = [dict(comments=str(bug))]
        return paths, jsons

    def _create_certificates(self, paths, jsons, bug, repeat_delta):
        app.logger.debug(fmt('_create_certificates:\n{locals}'))
        order_ids, request_ids = self._order_certificates(paths, jsons)
        self._update_requests_status(request_ids, 'approved', bug)
        calls = self._get_certificate_order_detail(order_ids)
        certificate_ids = [call.recv.json.certificate.id for call in calls]
        try:
            crts = self._download_certificates(certificate_ids, repeat_delta=repeat_delta)
            calls = self._get_certificate_order_detail(order_ids)
            expiries = [expiryify(call) for call in calls]
        except DownloadCertificateError as dce:
            app.logger.warning(str(dce))
            crt = None
            expiry = None
        return crts, expiries, order_ids

    def _revoke_certificates(self, paths, jsons, bug):
        app.logger.debug(fmt('_revoke_certificates:\n{locals}'))
        calls = self.puts(paths=paths, jsons=jsons)
        for call in calls:
            if call.recv.status != 201:
                raise RevokeCertificateError(call)
        request_ids = [call.recv.json.id for call in calls]
        self._update_requests_status(request_ids, 'approved', bug)

    def _order_certificates(self, paths, jsons):
        app.logger.debug(fmt('_order_certificates:\n{locals}'))
        calls = self.posts(paths=paths, jsons=jsons)
        for call in calls:
            if call.recv.status != 201:
                raise OrderCertificateError(call)
        return zip(*[(call.recv.json.id, call.recv.json.requests[0].id) for call in calls])

    def _update_requests_status(self, request_ids, status,bug):
        app.logger.debug(fmt('_update_requests_status:\n{locals}'))
        paths = [fmt('request/{request_id}/status') for request_id in request_ids]
        jsons = [dict(status=status, processor_comment=bug)]
        app.logger.debug(fmt('calling digicert api with paths={paths} and jsons={jsons}'))
        calls = self.puts(paths=paths, jsons=jsons)
        for call in calls:
            if call.recv.status != 204:
                if call.recv.json.errors[0].code != 'request_already_processed':
                    raise ApproveCertificateError(call)
        return True

    def _get_certificate_order_summary(self):
        app.logger.debug(fmt('_get_certificate_order_summary:\n{locals}'))
        call = self.get(path='order/certificate')
        return call

    def _get_certificate_order_detail(self, order_ids):
        app.logger.debug(fmt('_get_certificate_order_detail:\n{locals}'))
        paths = [fmt('order/certificate/{order_id}') for order_id in order_ids]
        calls = self.gets(paths=paths)
        return calls

    def _download_certificates(self, certificate_ids, format_type='pem_noroot', repeat_delta=None):
        app.logger.debug(fmt('_download_certificates:\n{locals}'))
        if repeat_delta is not None and isinstance(repeat_delta, int):
            repeat_delta = timedelta(seconds=repeat_delta)
        paths = [fmt('certificate/{certificate_id}/download/format/{format_type}') for certificate_id in certificate_ids]
        calls = self.gets(paths=paths, repeat_delta=repeat_delta, repeat_if=not_200)
        texts = []
        for call in calls:
            if call.recv.status == 200:
                texts += [call.recv.text]
            else:
                raise DownloadCertificateError(call)
        return texts
