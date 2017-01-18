#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
asyncrequests
'''

from utils.format import fmt
from utils.asyncrequests import AsyncRequests

class AuthorityFactoryError(Exception):
    def __init__(self, authority):
        msg = fmt('authority factory error {authority}')

class AuthorityBase(AsyncRequests):
    def __init__(self, cfg, verbosity):
        self.cfg = cfg
        for k, v in cfg.items():
            setattr(self, k, v)
        self.verbosity = verbosity

    def display_certificate(self, cert_name):
        raise NotImplementedError

    def create_certificate(self, common_name, sans=None):
        raise NotImplementedError

    def renew_certificate(self, cert_name):
        raise NotImplementedError

    def revoke_certificate(self, cert_name):
        raise NotImplementedError

