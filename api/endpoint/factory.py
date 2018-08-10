#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from utils.fmt import fmt

from config import CFG

from app import app

from endpoint.list import ListEndpoint
from endpoint.query import QueryEndpoint
from endpoint.create import CreateEndpoint
from endpoint.update import UpdateEndpoint
from endpoint.revoke import RevokeEndpoint

method2endpoint = dict(
    GET=ListEndpoint,
    PUT=UpdateEndpoint,
    POST=CreateEndpoint,
    DELETE=RevokeEndpoint)

command2endpoint = dict(
    ls=ListEndpoint,
    query=QueryEndpoint,
    create=CreateEndpoint,
    deploy=UpdateEndpoint,
    renew=UpdateEndpoint,
    revoke=RevokeEndpoint)

def create_endpoint(method, cfg, args):
    if cfg is None:
        cfg = CFG
    endpoint = command2endpoint[args['command']]
    app.logger.debug(fmt('create_endpoint: endpoint={0} args={1}', endpoint, args))
    return endpoint(cfg, args)



