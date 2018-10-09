#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
autocert.create
'''

import os

from pprint import pformat
from attrdict import AttrDict
from datetime import timedelta

from endpoint.base import EndpointBase
from exceptions import AutocertError
from config import CFG
from utils.fmt import *
from utils import pki
from app import app

from bundle import Bundle

class UnknownCertificateAuthorityError(AutocertError):
    def __init__(self, authority):
        message = fmt('unknown certificate authority: {authority}')
        super(UnknownCertificateAuthorityError, self).__init__(message)

class CreateEndpoint(EndpointBase):
    def __init__(self, cfg, args):
        super(CreateEndpoint, self).__init__(cfg, args)

    def execute(self):
        status = 201
        modhash, key, csr = pki.create_modhash_key_and_csr(
            self.args.common_name,
            public_exponent=CFG.key.public_exponent,
            key_size=CFG.key.key_size,
            key=self.args.key,
            csr=self.args.csr,
            oids=self.cfg.csr.oids,
            sans=self.args.sans)
        crt, expiry, authority = self.authority.create_certificate(
            self.args.organization_name,
            self.args.common_name,
            self.args.validity_years,
            csr,
            self.args.bug,
            sans=sorted(list(self.args.sans)),
            repeat_delta=self.args.repeat_delta,
            whois_check=self.args.whois_check)
        bundle = Bundle(
            self.args.common_name,
            modhash,
            key,
            csr,
            crt,
            self.args.bug,
            sans=sorted(list(self.args.sans)),
            expiry=expiry,
            authority=authority)
        bundle.to_disk()
        if self.args.destinations:
            note = 'bug ' + bug
            for name, dests in self.args.destinations.items():
                bundle = self.destinations[name].install_certificates(note, [bundle], *dests)[0]
        json = self.transform([bundle])
        return json, status
