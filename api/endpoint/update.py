#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
autocert.update
'''

from pprint import pformat
from attrdict import AttrDict
from flask import make_response, jsonify, request

from utils import tar

#from autocert import show

from utils import pki

try:
    from autocert.app import app
except ImportError:
    from app import app

from config import CFG

class MissingUpdateArgumentsError(Exception):
    def __init__(self, args):
        msg = 'missing arguments to update; args = {0}'.format(args)
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
        raise NotImplementedError

    def respond(self, **kwargs):
        raise NotImplementedError

#def renew(cert_name, authority, **kwargs):
#    app.logger.info('update.renew:\n{0}'.format(pformat(locals())))
#    return {'certs': []}
#
#def deploy(cert_name, destinations, verbosity, **kwargs):
#    common_name, suffix, authority_code, order_id = pki.decompose_cert_name(cert_name)
#    key, csr, crt = tar.untar_cert_files(cert_name)
#    if not crt:
#        if authority_code == 'dc':
#            crt = digicert.download_certificate(order_id)
#        elif authority_code == 'le':
#            raise NotImplementedError
#    app.logger.info('update.deploy:\n{0}'.format(pformat(locals())))
#    if 'zeus' in destinations:
#        zeus.put_certificate(common_name, crt, csr, key, cert_name, *destinations['zeus'])
#        json, status_code = show.show(common_name=common_name, verbosity=verbosity)
#        if status_code != 200:
#            return json, status_code
#        return json, 201
#    raise DeployError
#
#def update(**kwargs):
#    app.logger.info('update: {0}'.format(locals()))
#    if kwargs.get('authority', None):
#        return renew(**kwargs)
#    elif kwargs.get('destinations', None):
#        return deploy(**kwargs)
#    raise MissingUpdateArgumentsError(args)
#
