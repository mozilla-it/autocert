#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from utils.asyncrequests import AsyncRequests

class DestinationBase(AsyncRequests):
    def __init__(self, cfg, verbosity):
        self.cfg = cfg
        self.verbosity = verbosity

    def fetch_certificate(self, common_name, *dests, csr=None):
        raise NotImplementedError

    def install_certificate(self, common_name, crt, csr, key, note, *dests):
        raise NotImplementedError

    def update_certificate(self, common_name, crt, note, *dests):
        raise NotImplementedError

    def remove_certificate(self, common_name, csr, *dests):
        raise NotImplementedError
