#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from utils.format import fmt

from config import CFG

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

def create_endpoint(method, cfg, args):
    if cfg is None:
        cfg = CFG
    endpoint = method2endpoint[method]
    app.logger.debug(fmt('create_endpoint: endpoint={0} args={1}', endpoint, args))
    return endpoint(cfg, args)



