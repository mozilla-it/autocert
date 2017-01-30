#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

from pprint import pformat, pprint
from attrdict import AttrDict
from fnmatch import fnmatch
from ruamel import yaml

from autocert import digicert
from autocert import zeus
from utils import tar

from utils.dictionary import merge, head, head_body

from app import app

from config import CFG

from endpoint.base import EndpointBase
from authority.factory import create_authority

class DisplayEndpoint(EndpointBase):
    def __init__(self, cfg, verbosity):
        super(DisplayEndpoint, self).__init__(cfg, verbosity)

    def execute(self, **kwargs):
        status = 200
        authority = create_authority('digicert', self.ar, self.cfg['authorities']['digicert'], self.verbosity) #FIXME: this should be better
        cert_name_pns = [self.sanitize(cert_name_pn) for cert_name_pn in self.args.cert_name_pns]
        certs = self.tardata.get_certdata_from_tarfiles(*cert_name_pns)
        if self.verbosity > 3:
            certs = authority.display_certificates(certs)
        json = self.transform(certs)
        return json, status
