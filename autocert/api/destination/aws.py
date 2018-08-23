#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from destination.base import DestinationBase
from config import CFG

class AwsDestination(DestinationBase):
    def __init__(self, ar, cfg, verbosity=0):
        super(AwsDestination, self).__init__(ar, cfg, verbosity)

    def fetch_certificate(self, certs, *dests):
        raise NotImplementedError

    def install_certificate(self, certs, *dests):
        raise NotImplementedError

    def update_certificate(self, certs, *dests):
        raise NotImplementedError

    def remove_certificate(self, certs, *dests):
        raise NotImplementedError
