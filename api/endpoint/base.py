#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from config import CFG

from authority.factory import create_authority
from destination.factory import create_destination

class EndpointBase(object):
    def __init__(self, cfg, verbosity):
        authorities = cfg['authorities']
        destinations = cfg['destinations']
        self.authorities = {a: create_authority(a, authorities[a], verbosity) for a in authorities.keys()}
        self.destinations = {d: create_destination(d, destinations[d], verbosity) for d in destinations.keys()}
        self.verbosity = verbosity

    def execute(self, **kwargs):
        raise NotImplementedError

    def respond(self, **kwargs):
        raise NotImplementedError

