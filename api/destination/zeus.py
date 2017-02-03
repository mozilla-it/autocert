#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from destination.base import DestinationBase
from config import CFG

from utils.dictionary import merge, head, body
from utils.newline import windows2unix

class ZeusDestination(DestinationBase):
    def __init__(self, ar, cfg, verbosity):
        super(ZeusDestination, self).__init__(ar, cfg, verbosity)

    def fetch_certificates(self, certs, *dests):
        details = self._get_installed_certificates_details(certs, *dests)
        if details:
            for cert in certs:
                cert_body = body(cert)
                common_name = cert_body['common_name']
                tardata_body = body(cert_body['tardata'])
                crt_filename = keys_ending(tardata_body, 'crt')[0]
                csr_filename = keys_ending(tardata_body, 'csr')[0]
                key_filename = keys_ending(tardata_body, 'key')[0]
                crt = tardata_body[crt_filename]
                csr = tardata_body[csr_filename]
                key = tardata_body[key_filename]
                for dest, note in details.get((common_name, crt, csr), []):
                    cert['destinations'] = cert.get('destinations', {})
                    cert['destinations'][dest] = dict(
                        crt=crt,
                        csr=csr,
                        key=key,
                        note=note)
        return certs

    def install_certificate(self, common_name, crt, csr, key, note, *dests):
        paths = ['ssl/server_keys/' + common_name]
        calls = self.puts(paths=paths, dests=dests, json=dict(
            properties=dict(
                basic=dict(
                    public=crt,
                    request=csr,
                    private=key,
                    note=note))))
        return calls

    def update_certificates(self, certs, *dests):
        raise NotImplementedError

    def remove_certificates(self, certs, *dests):
        raise NotImplementedError

    def _get_installed_summary(self, certs, *dests):
        common_names = [body(cert)['common_name'] for cert in certs]
        paths = ['ssl/server_keys']
        calls = self.gets(paths=paths, dests=dests, verify_ssl=False)
        summary = []
        for dest, call in zip(dests, calls):
            for child in call.recv.json.children:
                if child.name in common_names:
                    summary += [(child.name, 'ssl/server_keys/' + child.name, dest)]
        return summary

    def _get_installed_certificates_details(self, certs, *dests):
        summary = self._get_installed_summary(certs, *dests)
        details = {}
        if summary:
            common_names, paths, dests = zip(*summary)
            calls = self.gets(paths=paths, dests=dests)
            for common_name, path, dest, call in zip(common_names, paths, dests, calls):
                crt = windows2unix(call.recv.json.properties.basic.public)
                csr = windows2unix(call.recv.json.properties.basic.request)
                key = windows2unix(call.recv.json.properties.basic.private)
                note = call.recv.json.properties.basic.note
                details[(common_name, crt, csr)] = details.get((common_name, crt, csr), []) + [(dest, note)]
        return details

