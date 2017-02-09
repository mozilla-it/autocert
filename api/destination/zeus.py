#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from destination.base import DestinationBase
from config import CFG

from utils.dictionary import merge, head, body, head_body, keys_ending
from utils.newline import windows2unix

from app import app
from utils.output import yaml_format

from cert import decompose_cert

def compose_json(crt, csr, key, note):
    return dict(properties=dict(basic=dict(
        crt=crt,
        csr=csr,
        key=key,
        note=note)))

class ZeusDestination(DestinationBase):
    def __init__(self, ar, cfg, verbosity):
        super(ZeusDestination, self).__init__(ar, cfg, verbosity)

    def fetch_certificates(self, certs, *dests):
        details = self._get_installed_certificates_details(certs, *dests)
        if details:
            for cert in certs:
                cert_name, common_name, crt, csr, key = decompose_cert(cert)
                destinations = details.get((common_name, crt[:40]), None)
                if destinations:
                    cert[cert_name]['destinations'] = cert[cert_name].get('destinations', {})
                    cert[cert_name]['destinations'].update(destinations)
        return certs

    def install_certificates(self, certs, *dests):
        paths, jsons = zip(*[('ssl/server_keys/' + common_name, compose_json(crt, csr, key, cert_name)) for cert_name, common_name, crt, csr, key in [decompose_cert(cert) for cert in certs]])

        print('paths =', paths)
        print('jsons =', yaml_format(jsons))
        calls = self.puts(paths=paths, dests=dests, jsons=jsons, verify_ssl=False)
        #FIXME: seems like there could be a better way...
        print('calls =', yaml_format(calls))
        certs = self.fetch_certificates(certs, *dests)
        return certs

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
            calls = self.gets(paths=paths, dests=dests, verify_ssl=False)
            for common_name, path, dest, call in zip(common_names, paths, dests, calls):
                crt = windows2unix(call.recv.json.properties.basic.public)
                csr = windows2unix(call.recv.json.properties.basic.request)
                key = windows2unix(call.recv.json.properties.basic.private)
                note = call.recv.json.properties.basic.note
                details[(common_name, crt[:40])] = details.get((common_name, crt[:40]), {})
                details[(common_name, crt[:40])][dest] = dict(
                    crt=crt,
                    csr=csr,
                    key=key,
                    note=note)
        return details

