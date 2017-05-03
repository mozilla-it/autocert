#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from destination.base import DestinationBase
from config import CFG

from utils.dictionary import merge, head, body, head_body, keys_ending
from utils.newline import windows2unix

from app import app
from utils.output import yaml_format

from utils.format import fmt, pfmt


ZEUS_PATH = 'ssl/server_keys/'

def compose_json(key, csr, crt, note):
    return dict(properties=dict(basic=dict(
        private=key,
        request=csr,
        public=crt,
        note=note)))

class ZeusDestination(DestinationBase):
    def __init__(self, ar, cfg, verbosity):
        super(ZeusDestination, self).__init__(ar, cfg, verbosity)

    def fetch_certificates(self, certs, *dests):
        details = self._get_installed_certificates_details(certs, *dests)
        if details:
            for cert in certs:
                detail_key = (cert.common_name, cert.crt[:40])
                destinations = details.get(detail_key, {})
                if destinations:
                    for dest, (key, csr, crt, note) in destinations.items():
                        zeus_detail = cert.destinations.get('zeus', {})
                        matched = csr == cert.csr and crt == cert.crt
                        zeus_detail[dest] = dict(
                            matched=matched,
                            note=note)
                        cert.destinations['zeus'] = zeus_detail
        return certs

    def install_certificates(self, note, certs, *dests):
        paths, jsons = zip(*[(ZEUS_PATH+cert.common_name, compose_json(cert.key, cert.csr, cert.crt, note)) for cert in certs])
        calls = self.puts(paths=paths, dests=dests, jsons=jsons, verify_ssl=False)
        certs = self.fetch_certificates(certs, *dests)
        return certs

    def update_certificates(self, certs, *dests):
        raise NotImplementedError

    def remove_certificates(self, certs, *dests):
        raise NotImplementedError

    def _get_installed_summary(self, certs, *dests):
        common_names = [cert.common_name for cert in certs]
        calls = self.gets(paths=[ZEUS_PATH], dests=dests, verify_ssl=False)
        assert len(dests) == len(calls)
        summary = []
        for dest, call in zip(dests, calls):
            app.logger.debug(fmt('dest={dest} call=\n{call}'))
            for child in call.recv.json.children:
                if child.name in common_names:
                    summary += [(child.name, ZEUS_PATH+child.name, dest)]
        return summary

    def _get_installed_certificates_details(self, certs, *dests):
        summary = self._get_installed_summary(certs, *dests)
        details = {}
        if summary:
            common_names, paths, dests = zip(*summary)
            calls = self.gets(paths=paths, dests=dests, product=False, verify_ssl=False)
            for common_name, path, dest, call in zip(common_names, paths, dests, calls):
                try:
                    crt = windows2unix(call.recv.json.properties.basic.get('public', 'missing'))
                    csr = windows2unix(call.recv.json.properties.basic.get('request', 'missing'))
                    key = windows2unix(call.recv.json.properties.basic.get('private', 'missing'))
                    note = call.recv.json.properties.basic.get('note', '')
                except Exception as ex:
                    app.logger.debug(fmt('call.send.url={0}', call.send.url))
                    app.logger.debug(fmt('call.recv.json=\n{0}', call.recv.json))
                details[(common_name, crt[:40])] = details.get((common_name, crt[:40]), {})
                details[(common_name, crt[:40])][dest] = (
                    key,
                    csr,
                    crt,
                    note)
        return details

