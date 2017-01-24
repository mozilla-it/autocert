#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from attrdict import AttrDict

class DestinationPathNotSetError(Exception):
    def __init__(self):
        msg = 'destination path not set'
        super(DestinationPathNotSetError, self).__init__(msg)

class DestinationDestsNotSetError(Exception):
    def __init__(self):
        msg = 'destination dests not set'
        super(DestinationDestsNotSetError, self).__init__(msg)

class DestinationBase(object):
    def __init__(self, ar, cfg, verbosity):
        self.ar = ar
        self.cfg = AttrDict(cfg)
        self.verbosity = verbosity

    def request(self, method, path=None, dests=None, **kw):
        if not path:
            raise DestinationPathNotSetError
        if not dests:
            raise DestinationDestsNotSetError
        kws = []
        for dest in dests:
            cfg = self.cfg[dest]
            kws += [copy.deepcopy(kw)]
            kws[-1]['url'] = cfg['baseurl'] / path
            kws[-1]['auth'] = kws[-1].pop('auth', cfg['auth'])
            kws[-1]['headers'] = kws[-1].pop('headers', cfg['headers'])
        return self.ar.requests(method, *kws)

    def get(self, path=None, dests=None, **kw):
        return self.request('GET', path=path, dests=dests, **kw)

    def put(self, path=None, dests=None, **kw):
        return self.request('PUT', path=path, dests=None, **kw)

    def post(self, path=None, dests=None, **kw):
        return self.request('POST', path=path, dests=dests, **kw)

    def delete(self, path=None, dests=None, **kw):
        return self.request('DELETE', path=path, dests=dests, **kw)

    def fetch_certificate(self, common_name, *dests, csr=None):
        raise NotImplementedError

    def install_certificate(self, common_name, crt, csr, key, note, *dests):
        raise NotImplementedError

    def update_certificate(self, common_name, crt, note, *dests):
        raise NotImplementedError

    def remove_certificate(self, common_name, csr, *dests):
        raise NotImplementedError
