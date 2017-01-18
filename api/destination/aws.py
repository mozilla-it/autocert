#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from destination.base import DestinationBase
from config import CFG

class AwsDestination(DestinationBase):
    def __init__(self, verbosity=0, config=None):
        if config == None:
            config = CFG.destinations.aws
        super(AwsDestination, self).__init__(verbosity, config)

    def fetch_certificate(self, common_name, *dests, csr=None):
        raise NotImplementedError

    def install_certificate(self, common_name, crt, csr, key, note, *dests):
        raise NotImplementedError

    def update_certificate(self, common_name, crt, note, *dests):
        raise NotImplementedError

    def remove_certificate(self, common_name, csr, *dests):
        raise NotImplementedError
