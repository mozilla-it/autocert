#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import make_response, jsonify
from attrdict import AttrDict

from tardata import Tardata
from authority.factory import create_authority
from destination.factory import create_destination
from utils.asyncrequests import AsyncRequests

class EndpointBase(object):
    def __init__(self, cfg, args):
        self.ar = AsyncRequests()
        self.cfg = AttrDict(cfg)
        self.args = AttrDict(args)
        self.verbosity = self.args.verbosity
        authorities = self.cfg.authorities
        self.authorities = {
            a: create_authority(a, self.ar, authorities[a], self.verbosity) for a in authorities
        }
        destinations = self.cfg.destinations
        self.destinations = {
            d: create_destination(d, self.ar, destinations[d], self.verbosity) for d in destinations
        }
        self.tardata = Tardata(self.cfg.tar.dirpath, self.verbosity)

    @property
    def calls(self):
        return self.ar.calls

    def execute(self, **kwargs):
        raise NotImplementedError

    def respond(self, json, status):
        return make_response(jsonify(json), status)
