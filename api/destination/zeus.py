#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from destination.base import DestinationBase
from config import CFG

class ZeusDestination(DestinationBase):
    def __init__(self, ar, cfg, verbosity):
        super(ZeusDestination, self).__init__(ar, cfg, verbosity)

    def fetch_certificate(self, common_name, *dests, csr=None):
        raise NotImplementedError

    def install_certificate(self, common_name, crt, csr, key, note, *dests):
        raise NotImplementedError

    def update_certificate(self, common_name, crt, note, *dests):
        raise NotImplementedError

    def remove_certificate(self, common_name, csr, *dests):
        raise NotImplementedError

    def _get_installed_certificates_summary(self, *dests):
        paths = ['ssl/server_keys']
        calls = self.gets(paths=paths, dests=dests, verify_ssl=False)
        summary = {}
        for dest, call in zip(dests, calls):
            summar[dest] = {}
            for child in call.recv.json.children:
                summary[dest][child.name] = child.href
        return summary
