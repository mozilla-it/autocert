#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app.endpoint.list import ListEndpoint
from app.endpoint.query import QueryEndpoint
from app.endpoint.create import CreateEndpoint
from app.endpoint.update import UpdateEndpoint
from app.endpoint.revoke import RevokeEndpoint

from app.app import app
from app.config import CFG
from app.utils.fmt import *

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



