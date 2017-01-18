#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from utils.format import fmt

from config import CFG

try:
    from autocert.app import app
except ImportError:
    from app import app

from endpoint.create import CreateEndpoint
from endpoint.display import DisplayEndpoint
from endpoint.update import UpdateEndpoint
from endpoint.revoke import RevokeEndpoint

method2endpoint = dict(
    GET=DisplayEndpoint,
    PUT=UpdateEndpoint,
    POST=CreateEndpoint,
    DELETE=RevokeEndpoint)

def create_endpoint(method, cfg, verbosity):
    if cfg is None:
        cfg = CFG
    endpoint = method2endpoint[method]
    app.logger.debug(fmt('create_endpoint: verbosity={0} endpoint={1}', verbosity, endpoint))
    return endpoint(cfg, verbosity)



