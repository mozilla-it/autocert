#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from itertools import product
from attrdict import AttrDict

from utils.format import fmt

class DestinationPathError(Exception):
    def __init__(self, path_or_paths):
        msg = fmt('error with DestinationBase param path(s) = {path_or_paths}')
        super(DestinationPathError, self).__init__(msg)

class DestinationDestError(Exception):
    def __init__(self, dest_or_dests):
        msg = fmt('error with DestinationBase param dest(s) = {dest_or_dests}')
        super(DestinationDestError, self).__init__(msg)

class DestinationBase(object):
    def __init__(self, ar, cfg, verbosity):
        self.ar = ar
        self.cfg = AttrDict(cfg)
        self.verbosity = verbosity

    def keywords(self, path=None, dest=None, **kw):
        if not path:
            raise DestinationPathError(path)
        if not dest:
            raise DestinationDestError(dest)
        cfg = AttrDict(self.cfg[dest])
        kw['url'] = str(cfg.baseurl / path)
        kw['auth'] = kw.get('auth', cfg.auth)
        kw['headers'] = kw.get('headers', cfg.headers)
        return kw

    def request(self, method, **kw):
        self.ar.request(method, **self.keywords(**kw))

    def get(self, path=None, dest=None, **kw):
        return self.request('GET', path=path, dest=dest, **kw)

    def put(self, path=None, dest=None, **kw):
        return self.request('PUT', path=path, dest=dest, **kw)

    def post(self, path=None, dest=None, **kw):
        return self.request('POST', path=path, dest=dest, **kw)

    def delete(self, path=None, dest=None, **kw):
        return self.request('DELETE', path=path, dest=dest, **kw)

    def requests(self, method, paths=None, dests=None, **kw):
        if not paths or not isinstance(paths, list):
            raise DestinationPathsError(paths)
        if not dests or not isinstance(paths, list):
            raise DestinationDestsError(dests)
        kws = [self.keywords(path=path, dest=dest, **kw) for path, dest in product(paths, dests)]
        return self.ar.requests(method, *kws)

    def gets(self, paths=None, dests=None, **kw):
        return self.requests('GET', paths=paths, dests=dests, **kw)

    def puts(self, paths=None, dests=None, **kw):
        return self.requests('PUT', paths=paths, dests=dests, **kw)

    def posts(self, paths=None, dests=None, **kw):
        return self.requests('POST', paths=paths, dests=dests, **kw)

    def deletes(self, paths=None, dests=None, **kw):
        return self.requests('DELETE', paths=paths, dests=dests, **kw)

    def fetch_certificate(self, certs, *dests):
        raise NotImplementedError

    def install_certificate(self, common_name, crt, csr, key, note, *dests):
        raise NotImplementedError

    def update_certificate(self, certs, *dests):
        raise NotImplementedError

    def remove_certificate(self, certs, *dests):
        raise NotImplementedError
