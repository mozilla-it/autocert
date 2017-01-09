#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pprint, pformat
from attrdict import AttrDict
from fnmatch import fnmatch
from ruamel import yaml
from flask import jsonify

from autocert import digicert
from autocert import zeus
from autocert import tar

from autocert.utils.dictionary import merge, head, body

try:
    from autocert.app import app
except ImportError:
    from app import app

try:
    from autocert.config import CFG
except ImportError:
    from config import CFG

def show(common_name, verbosity, suffix=None, **kwargs):
    app.logger.info('show: {0}'.format(locals()))
    digicert_certs = digicert.get_active_certificate_orders_and_details(common_name)
    certs = []
    for cert in digicert_certs:
        cert_name = head(cert)
        cert_body = body(cert)
        if suffix and suffix != cert_body['suffix']:
            continue
        else:
            csr = cert_body['authorities']['digicert']['csr']
            common_name = cert_body['common_name']
            installed = zeus.get_installed_certificates(csr, common_name, *list(CFG.destinations.zeus.keys()))
            cert = merge(cert, {cert_name: installed.get(common_name, {})})
            cert = merge(cert, tar.get_records_from_tarfiles(cert_name))
            certs += [cert]
    return {'certs': certs}, 200
