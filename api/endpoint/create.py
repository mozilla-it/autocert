#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from pprint import pformat
from attrdict import AttrDict
from datetime import timedelta

from utils.format import fmt
from utils import tar, pki

from app import app

from endpoint.base import EndpointBase

class UnknownCertificateAuthorityError(Exception):
    def __init__(self, authority):
        msg = fmt('unknown certificate authority: {authority}')
        super(UnknownCertificateAuthorityError, self).__init__(msg)

class CreateEndpoint(EndpointBase):
    def __init__(self, cfg, args):
        super(CreateEndpoint, self).__init__(cfg, args)

    @property
    def authority(self):
        return self.authorities[self.args.authority]

    def execute(self):
        status = 201
        key, csr = pki.create_key_and_csr(self.args.common_name, self.args.sans)
        crt, cert = self.authority.create_certificate(
            self.args.common_name,
            self.timestamp,
            csr,
            self.args.sans,
            self.args.repeat_delta)
        cert_name = pki.create_cert_name(self.args.common_name, self.timestamp)
        tarfile = tar.bundle(self.cfg.tar.dirpath, cert_name, key, csr, crt, cert)
        cert = self.tardata.create_certdata(cert_name, key, csr, crt, cert)
        if self.args.destinations:
            for name, dests in self.args.destinations.items():
                cert = self.destinations[name].install_certificate(self.args.common_name, crt, csr, key, cert_name, *dests)
        json = self.transform([cert])
        return json, status
