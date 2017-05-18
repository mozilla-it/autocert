#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pformat
from utils import blacklist
from utils.exceptions import AutocertError

from app import app

from endpoint.base import EndpointBase

class RevokeEndpoint(EndpointBase):
    def __init__(self, cfg, verbosity):
        super(RevokeEndpoint, self).__init__(cfg, verbosity)

    def execute(self, **kwargs):
        status = 202
        cert_name_pns = [self.sanitize(cert_name_pn) for cert_name_pn in self.args.cert_name_pns]
        certs = self.tardata.load_certs(*cert_name_pns)
        blacklist.check(certs, self.args.blacklist_overrides)
        certs = self.authority.revoke_certificates(
            certs,
            self.args.bug)
        for cert in certs:
            cert.expiry = self.tardata.timestamp
            self.tardata.update_cert(cert)
        json = self.transform(certs)
        return json, status

