#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pprint, pformat
from attrdict import AttrDict
from fnmatch import fnmatch
from ruamel import yaml
from flask import jsonify

from autocert import digicert
from autocert import zeus
from utils import tar

from utils.dictionary import merge, head, body

try:
    from autocert.app import app
except ImportError:
    from app import app

from config import CFG

from endpoint.base import EndpointBase

class DisplayEndpoint(EndpointBase):
    def __init__(self, cfg, verbosity):
        super(DisplayEndpoint, self).__init__(cfg, verbosity)

    def execute(self, **kwargs):
        #raise NotImplementedError
        pass

    def respond(self, **kwargs):
        raise NotImplementedError
        return { 'certs': []}, 200

#def display(common_name, verbosity, suffix=None, **kwargs):
#    app.logger.info('display: {0}'.format(locals()))
#    digicert_certs = digicert.get_active_certificate_orders_and_details(common_name)
#    certs = []
#    for cert in digicert_certs:
#        cert_name = head(cert)
#        cert_body = body(cert)
#        if suffix and suffix != cert_body['suffix']:
#            continue
#        else:
#            csr = cert_body['authorities']['digicert']['csr']
#            common_name = cert_body['common_name']
#            installed = zeus.get_installed_certificates(csr, common_name, *list(CFG.destinations.zeus.keys()))
#            cert = merge(cert, {cert_name: installed.get(common_name, {})})
#            cert = merge(cert, tar.get_records_from_tarfiles(cert_name))
#            certs += [cert]
#    return {'certs': certs}, 200
