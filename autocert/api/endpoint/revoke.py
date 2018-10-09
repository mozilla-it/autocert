#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from endpoint.base import EndpointBase
from exceptions import AutocertError
from pprint import pformat
from app import app
import blacklist

class RevokeEndpoint(EndpointBase):
    def __init__(self, cfg, verbosity):
        super(RevokeEndpoint, self).__init__(cfg, verbosity)

    def execute(self, **kwargs):
        status = 202
        bundle_name_pns = [self.sanitize(cert_name_pn) for cert_name_pn in self.args.bundle_name_pns]
        bundles = Bundle.bundles(bundle_name_pns)
        blacklist.check(bundles, self.args.blacklist_overrides)
        bundles = self.authority.revoke_certificates(
            bundles,
            self.args.bug)
        for bundle in bundles:
            bundle.expiry = Bundle.timestamp
            bundle.to_disk()
        json = self.transform(bundles)
        return json, status

