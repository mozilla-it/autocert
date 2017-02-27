#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pformat

from endpoint.base import EndpointBase

class RevokeEndpoint(EndpointBase):
    def __init__(self, cfg, verbosity):
        super(RevokeEndpoint, self).__init__(cfg, verbosity)

    def execute(self, **kwargs):
        raise NotImplementedError
