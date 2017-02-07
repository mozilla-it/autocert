#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pformat, pprint

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

class JsonsDontMatchPathsError(Exception):
    def __init__(self, jsons, paths):
        len_jsons = len(jsons) if isinstance(jsons, list) else None
        len_paths = len(paths) if isinstance(paths, list) else None
        msg = fmt('len(jsons) -> {len_jsons} != len(paths) -> {len_paths}; jsons={jsons}, paths={paths}')
        super(JsonsDontMatchPathsError, self).__init__(msg)

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

    def requests(self, method, paths=None, dests=None, jsons=None, **kw):
        if not paths or not hasattr(paths, '__iter__'):
            raise DestinationPathError(paths)
        if not dests or not hasattr(dests, '__iter__'):
            raise DestinationDestError(dests)
        if jsons:
            if len(jsons) != len(paths):
                raise JsonsDontMatchPathsError(jsons, paths)
            kws = [self.keywords(path=path, dest=dest, json=json, **kw) for (path, json), dest in product(zip(paths, jsons), dests)]
        else:
            kws = [self.keywords(path=path, dest=dest, **kw) for path, dest in product(paths, dests)]
        return self.ar.requests(method, *kws)

    def gets(self, paths=None, dests=None, jsons=None, **kw):
        return self.requests('GET', paths=paths, dests=dests, jsons=jsons, **kw)

    def puts(self, paths=None, dests=None, jsons=None, **kw):
        return self.requests('PUT', paths=paths, dests=dests, jsons=jsons, **kw)

    def posts(self, paths=None, dests=None, jsons=None, **kw):
        return self.requests('POST', paths=paths, dests=dests, jsons=jsons, **kw)

    def deletes(self, paths=None, dests=None, jsons=None, **kw):
        return self.requests('DELETE', paths=paths, dests=dests, jsons=jsons, **kw)

    def add_destinations(self, cert, *dests, **items):
        '''
        does this belong here?
        '''
        cert['destinations'] = cert.get('destinations', {})
        for dest in dests:
            cert['destinations'][dest] = items
        return cert

    def fetch_certificates(self, certs, *dests):
        raise NotImplementedError

    def install_certificates(self, certs, *dests):
        raise NotImplementedError

    def update_certificates(self, certs, *dests):
        raise NotImplementedError

    def remove_certificates(self, certs, *dests):
        raise NotImplementedError
