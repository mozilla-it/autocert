#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
autocert.update
'''

from pprint import pformat
from attrdict import AttrDict

from utils.format import fmt, pfmt
from utils.output import yaml_format

from app import app

class MissingUpdateArgumentsError(Exception):
    def __init__(self, args):
        msg = fmt('missing arguments to update; args = {args}')
        super(MissingUpdateArgumentsError, self).__init__(msg)

class DeployError(Exception):
    def __init__(self):
        msg = 'deploy error; deployment didnt happen'
        super(DeployError, self).__init__(msg)

from endpoint.base import EndpointBase

class UpdateEndpoint(EndpointBase):
    def __init__(self, cfg, verbosity):
        super(UpdateEndpoint, self).__init__(cfg, verbosity)

    def execute(self, **kwargs):
        status = 201
        cert_name_pns = [self.sanitize(cert_name_pn) for cert_name_pn in self.args.cert_name_pns]
        certs = self.tardata.load_certs(self.timestamp, *cert_name_pns)
        if self.args.get('authority', None):
            certs = self.renew(certs, **kwargs)
        elif self.args.get('destinations', None):
            certs = self.deploy(certs, **kwargs)
        else:
            raise MissingUpdateArgumentsError(self.args)
        json = self.transform(certs)
        return json, status

    def renew(self, certs, **kwargs):
        count = len(certs) if certs else 0
        certs_str = yaml_format(certs)
        kwargs_str = yaml_format(kwargs)
        app.logger.info(fmt('renew: {count} certs={certs_str} kwargs={kwargs_str}'))
        return []

    def deploy(self, certs, **kwargs):
        installed_certs = []
        for name, dests in self.args.destinations.items():
            installed_certs += self.destinations[name].install_certificates(certs, *dests)
        return installed_certs
