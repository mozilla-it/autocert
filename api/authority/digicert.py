#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import zipfile
from attrdict import AttrDict
from pprint import pprint, pformat
from fnmatch import fnmatch
from datetime import timedelta #FIXME: do we import this here?
from whois import whois
from tld import get_tld
from utils import pki

from authority.base import AuthorityBase
from utils.dictionary import merge, body
from utils.format import fmt, pfmt
from utils.newline import windows2unix
from utils.exceptions import AutocertError

from app import app

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

class WhoisDoesntMatchError(AutocertError):
    def __init__(self, domains):
        domains = ', '.join(domains)
        message = fmt('list of domains with whois emails not matching hostmaster@mozilla.com: {domains}')
        super(WhoisDoesntMatchError, self).__init__(message)

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

    def create_certificate(self, organization_name, common_name, validity_years, bug, csr=None, sans=None, repeat_delta=None, no_whois_check=False):
        app.logger.info(fmt('create_certificate:\n{locals}'))
        modhash, key, csr = pki.create_modhash_key_and_csr(common_name, sans)
        if not sans:
            sans = []
        organization_id, container_id = self._get_organization_container_ids(organization_name)
        path, json = self._prepare_path_json(
            organization_id,
            container_id,
            common_name,
            validity_years,
            bug,
            csr,
            sans=sans,
            no_whois_check=no_whois_check)
        crts, expiries, order_ids = self._create_certificates([path], [json], bug, repeat_delta)
        authority = dict(digicert=dict(order_id=order_ids[0]))
        return modhash, key, csr, crts[0], expiries[0], authority

    def renew_certificates(self, certs, organization_name, validity_years, bug, sans=None, repeat_delta=None, no_whois_check=False):
        app.logger.info(fmt('renew_certificates:\n{locals}'))
        organization_id, container_id = self._get_organization_container_ids(organization_name)
        csrs = self._generate_csrs(certs, sans)
        paths, jsons = self._prepare_paths_jsons_for_re(
            certs,
            organization_id,
            container_id,
            bug,
            validity_years,
            is_reissue=False,
            no_whois_check=no_whois_check)
        crts, expiries, order_ids = self._create_certificates(paths, jsons, bug, repeat_delta)
        authorities = [dict(digicert=dict(order_id=order_id)) for order_id in order_ids]
        return csrs, crts, expiries, authorities

    def reissue_certificates(self, certs, organization_name, validity_years, bug, sans=None, repeat_delta=None, no_whois_check=False):
        app.logger.info(fmt('reissue_certificates:\n{locals}'))
        organization_id, container_id = self._get_organization_container_ids(organization_name)
        csrs = self._generate_csrs(certs, sans)
        paths, jsons = self._prepare_paths_jsons_for_re(
            certs,
            organization_id,
            container_id,
            bug,
            validity_years,
            is_reissue=True,
            no_whois_check=no_whois_check)
        crts, expiries, order_ids = self._create_certificates(paths, jsons, bug, repeat_delta)
        authorities = [dict(digicert=dict(order_id=order_id)) for order_id in order_ids]
        return csrs, crts, expiries, authorities

    def _generate_csrs(self, certs, sans):
        app.logger.info(fmt('_generate_csrs:\n{locals}'))
        csrs = []
        for cert in certs:
            cert.sans = combine_sans(cert.sans, sans)
            csr = pki.create_csr(cert.common_name, cert.key, sans=cert.sans)
            csrs += [csr]
            cert.csr = csr
        return csrs

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

    def _validate_domains(self, organization_id, container_id, domains, no_whois_check=False):
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

        def _whois_email(domain_to_check):
            app.logger.debug(fmt('_whois_email:\n{locals}'))
            try:
                emails = whois(domain_to_check)['emails']
                app.logger.debug(fmt('emails={emails}'))
                return 'hostmaster@mozilla.com' in emails
            except Exception as ex:
                app.logger.debug('WHOIS_ERROR')
                app.logger.debug(ex)
                return False
            return False

        not_whois_domains = []
        domains = list(set([get_tld('http://'+domain) for domain in domains]))
        if no_whois_check:
            app.logger.info('the whois check was defeated with --no-whois-check flag for this run')
        else:
            not_whois_domains = [domain for domain in domains if not _whois_email(domain)]
        if not_whois_domains:
            raise WhoisDoesntMatchError(not_whois_domains)
        denied_domains = [domain for domain in domains if not _is_validated(domain)]
        if denied_domains:
            raise NotValidatedDomainError(denied_domains)
        return True

    def _domains_to_check(self, common_name, sans):
        app.logger.debug(fmt('_domains_to_check:\n{locals}'))
        domains_to_check = [(common_name[2:] if common_name.startswith('*.') else common_name)]
        domains_to_check += sans if sans else []
        return list(set(domains_to_check))

    def _prepare_path_json(self, organization_id, container_id, common_name, validity_years, bug, csr, sans=None, is_reissue=False, order_id=None, no_whois_check=False):
        app.logger.debug(fmt('_prepare_path_json:\n{locals}'))
        domains_to_check = self._domains_to_check(common_name, sans)
        self._validate_domains(organization_id, container_id, domains_to_check, no_whois_check)
        order_path = 'order/certificate'
        path = fmt('{order_path}/ssl_plus')
        json = merge(self.cfg.template, dict(
            validity_years=validity_years,
            certificate=dict(
                common_name=common_name,
                csr=csr),
            organization=dict(
                id=organization_id),
            comments=bug))
        if common_name.startswith('*.'):
            path = fmt('{order_path}/ssl_wildcard')
        elif sans:
            path = fmt('{order_path}/ssl_multi_domain')
            json = merge(json, dict(
                certificate=dict(
                    dns_names=sans)))
        if order_id:
            if is_reissue:
                path = fmt('{order_path}/{order_id}/reissue')
            else:
                json = merge(json, dict(
                    renewal_of_order_id=order_id))
        return path, json

    def _prepare_paths_jsons_for_re(self, certs, organization_id, container_id, bug, validity_years, is_reissue, no_whois_check=False):
        app.logger.debug(fmt('_prepare_paths_jsons_for_re:\n{locals}'))
        paths = []
        jsons = []
        order_ids = [cert.authority['digicert']['order_id'] for cert in certs]
        calls = self._get_certificate_order_detail(order_ids)
        for cert, call, order_id in zip(certs, calls, order_ids):
            path, json = self._prepare_path_json(
                organization_id,
                container_id,
                cert.common_name,
                validity_years,
                bug,
                cert.csr,
                sans=cert.sans,
                is_reissue=is_reissue,
                order_id=order_id,
                no_whois_check=no_whois_check)
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
        self._ensure_order_not_processing(order_ids, repeat_delta=repeat_delta)
        calls = self._get_certificate_order_detail(order_ids)
        certificate_ids = [call.recv.json.certificate.id for call in calls]
        try:
            crts = self._download_certificates(certificate_ids, repeat_delta=repeat_delta)
            calls = self._get_certificate_order_detail(order_ids)
            expiries = [expiryify(call) for call in calls]
        except DownloadCertificateError as dce:
            app.logger.warning(str(dce))
            crts = []
            expiries = []
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
        app.logger.debug(fmt('calls={calls}'))
        for call in calls:
            if call.recv.status != 201:
                app.logger.debug(fmt('_order_certificates: call.recv.status = {0}', call.recv.status))
                raise OrderCertificateError(call)
        return zip(*[(call.recv.json.id, call.recv.json.requests[0].id) for call in calls])

    def _update_requests_status(self, request_ids, status, bug):
        app.logger.debug(fmt('_update_requests_status:\n{locals}'))
        paths = [fmt('request/{request_id}/status') for request_id in request_ids]
        jsons = [dict(status=status, processor_comment=bug)]
        app.logger.debug(fmt('calling digicert api with paths={paths} and jsons={jsons}'))
        calls = self.puts(paths=paths, jsons=jsons)
        app.logger.debug(fmt('calls={calls}'))
        for call in calls:
            if call.recv.status != 204:
                if call.recv.json.errors[0].code != 'request_already_processed':
                    raise ApproveCertificateError(call)
        return True

    def _ensure_order_not_processing(self, order_ids, repeat_delta=None):
        app.logger.debug(fmt('_ensure_order_not_processing:\n{locals}'))
        if repeat_delta is not None and isinstance(repeat_delta, int):
            repeat_delta = timedelta(seconds=repeat_delta)
        path='order/certificate?filters[status]=reissue_processing'
        def reissue_processing(call):
            app.logger.debug(fmt('reissue_processing:\n{locals}'))
            processing_ids = [order.id for order in call.recv.json.orders]
            is_reissue_processing = any([True for order_id in order_ids if order_id in processing_ids])
            app.logger.debug(fmt('FIXME: are any of order_ids={order_ids} in processing_ids={processing_ids} => {is_reissue_processing}'))
            return is_reissue_processing
        call = self.get(path=path, repeat_delta=repeat_delta, repeat_if=reissue_processing)
        if call.recv.status != 200:
            raise EnsureOrderNotProcessingError(order_ids)

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
        def not_200(call):
            return call.recv.status != 200
        paths = [fmt('certificate/{certificate_id}/download/format/{format_type}') for certificate_id in certificate_ids]
        calls = self.gets(paths=paths, repeat_delta=repeat_delta, repeat_if=not_200)
        texts = []
        for call in calls:
            if call.recv.status == 200:
                texts += [call.recv.text]
            else:
                raise DownloadCertificateError(call)
        return texts

