#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

from attrdict import AttrDict
from fnmatch import fnmatch
from ruamel import yaml

from utils.dictionary import merge, head, head_body
from utils.fmt import *
from app import app
from config import CFG
from endpoint.base import EndpointBase
from utils.yaml import yaml_format

from bundle import Bundle

class ListEndpoint(EndpointBase):
    def __init__(self, cfg, args):
        super(ListEndpoint, self).__init__(cfg, args)

    def execute(self, **kwargs):
        status = 200
        bundle_name_pns = [self.sanitize(bundle_name_pn) for bundle_name_pn in self.args.bundle_name_pns]
        bundles = Bundle.bundles(
            bundle_name_pns,
            within=self.args.within,
            expired=self.args.expired)
        bundles2 = []
        if self.verbosity > 1:
            #FIXME: this should be driven by the yml in the cert tarball
            bundles1 = self.authorities.digicert.display_certificates(bundles)
            for name, dests in self.args.destinations.items():
                pfmt('name={name} dests={dests}')
                bundles2.extend(self.destinations[name].fetch_certificates(bundles1, dests))
        else:
            bundles2 = bundles
        json = self.transform(bundles2)
        return json, status

