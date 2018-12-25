#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from asyncio import TimeoutError
from aiohttp import ClientConnectorError

from destination.base import DestinationBase, DestinationConnectivityError
from exceptions import AutocertError
from utils.dictionary import merge, head, body, head_body, keys_ending
from utils.newline import windows2unix
from utils.yaml import yaml_format
from config import CFG
from app import app

ZEUS_PATH = 'ssl/server_keys/'

def compose_json(key, csr, crt, note):
    return dict(properties=dict(basic=dict(
        private=key,
        request=csr,
        public=crt,
        note=note)))

class ZeusSSLServerKeysError(AutocertError):
    def __init__(self, call):
        message = f'zeus ssl/server_keys error call={call}'
        super(ZeusSSLServerKeysError, self).__init__(message)

class ZeusDestination(DestinationBase):
    def __init__(self, ar, cfg, verbosity):
        super(ZeusDestination, self).__init__(ar, cfg, verbosity)

    def has_connectivity(self, timeout, dests):
        app.logger.info(f'has_connectivity: locals={locals} dests={dests}')
        try:
            calls = self.gets(paths=[''], dests=dests, verify_ssl=False, timeout=timeout)
        except (TimeoutError, ClientConnectorError) as ex:
            dest_ex_pairs = []
            for dest in dests:
                try:
                    call = self.get(path='', dest=dest, verify_ssl=False, timeout=timeout)
                except (TimeoutError, ClientConnectorError) as ex:
                    dest_ex_pairs += [(dest, ex)]
            if dest_ex_pairs:
                raise DestinationConnectivityError(dest_ex_pairs)
        except Exception as ex:
            print('OOPS!', type(ex))
            print('Exception: ', ex)
            raise ex
        return True

    def fetch_certificates(self, bundles, dests):
        app.logger.info(f'fetch_certificates: bundles={bundles} dests={dests}')
        details = self._get_installed_certificates_details(bundles, dests)
        if details:
            for bundle in bundles:
                detail_key = (bundle.friendly_common_name, bundle.crt[:40])
                destinations = details.get(detail_key, {})
                if destinations:
                    for dest, (key, csr, crt, note) in destinations.items():
                        zeus_detail = bundle.destinations.get('zeus', {})
                        matched = crt == bundle.crt
                        zeus_detail[dest] = dict(
                            matched=matched,
                            note=note)
                        bundle.destinations['zeus'] = zeus_detail
        return bundles

    def install_certificates(self, note, bundles, dests):
        paths, jsons = zip(*[(ZEUS_PATH+bundle.friendly_common_name, compose_json(bundle.key, bundle.csr, bundle.crt, note)) for bundle in bundles])

        app.logger.info(f'install_certificates:\n{locals}')
        calls = self.puts(paths=paths, dests=dests, jsons=jsons, verify_ssl=False)
        bundles = self.fetch_certificates(bundles, dests)
        return bundles

    def update_certificates(self, bundles, dests):
        raise NotImplementedError

    def remove_certificates(self, bundles, dests):
        raise NotImplementedError

    def _get_installed_summary(self, bundles, dests):
        app.logger.debug(f'_get_installed_summary:\n{locals}')
        friendly_common_names = [bundle.friendly_common_name for bundle in bundles]
        calls = self.gets(paths=[ZEUS_PATH], dests=dests, timeout=10, verify_ssl=False)
        assert len(dests) == len(calls)
        summary = []
        for dest, call in zip(dests, calls):
            if call.recv.status != 200:
                raise ZeusSSLServerKeysError(call)
            for child in call.recv.json.children:
                if child.name in friendly_common_names:
                    summary += [(child.name, ZEUS_PATH+child.name, dest)]
        return summary

    def _get_installed_certificates_details(self, bundles, dests):
        app.logger.debug(f'_get_installed_certificates_details:\n{locals}')
        summary = self._get_installed_summary(bundles, dests)
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
                    app.logger.debug(f'call.send.url={call.send.url}')
                    app.logger.debug(f'call.recv.json=\n{call.recv.json}')
                    raise ex
                details[(common_name, crt[:40])] = details.get((common_name, crt[:40]), {})
                details[(common_name, crt[:40])][dest] = (
                    key,
                    csr,
                    crt,
                    note)
        return details

