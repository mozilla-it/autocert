#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
destination.base
'''
import itertools
from pprint import pformat
from attrdict import AttrDict

from exceptions import AutocertError
from utils.fmt import *
from app import app

class DestinationConnectivityError(AutocertError):
    def __init__(self, dest_ex_pairs):
        msg = ''
        for dest, ex in dest_ex_pairs:
            error = repr(ex)
            msg += fmt('{error} when attempting destination {dest}')
        super(DestinationConnectivityError, self).__init__(msg)

class DestinationPathError(AutocertError):
    def __init__(self, path_or_paths):
        message = fmt('error with DestinationBase param path(s) = {path_or_paths}')
        super(DestinationPathError, self).__init__(message)

class DestinationDestError(AutocertError):
    def __init__(self, dest_or_dests):
        message = fmt('error with DestinationBase param dest(s) = {dest_or_dests}')
        super(DestinationDestError, self).__init__(message)

class JsonsDontMatchPathsError(AutocertError):
    def __init__(self, jsons, paths):
        len_jsons = len(jsons) if isinstance(jsons, list) else None
        len_paths = len(paths) if isinstance(paths, list) else None
        message = fmt('len(jsons) -> {len_jsons} != len(paths) -> {len_paths}; jsons={jsons}, paths={paths}')
        super(JsonsDontMatchPathsError, self).__init__(message)

class DestsDontMatchPathsError(AutocertError):
    def __init__(self, dests, paths):
        len_dests = len(dests) if isinstance(dests, list) else None
        len_paths = len(paths) if isinstance(paths, list) else None
        message = fmt('len(dests) -> {len_dests} != len(paths) -> {len_paths}; dests={dests}, paths={paths}')
        super(DestsDontMatchPathsError, self).__init__(message)

class DestinationBase(object):
    def __init__(self, ar, cfg, verbosity):
        self.ar = ar
        self.cfg = AttrDict(cfg)
        self.verbosity = verbosity

    def keywords(self, path=None, dest=None, **kw):
        if path is None:
            raise DestinationPathError(path)
        if not dest:
            raise DestinationDestError(dest)
        cfg = AttrDict(self.cfg[dest])
        kw['url'] = str(cfg.baseurl / path)
        kw['auth'] = kw.get('auth', cfg.auth)
        kw['headers'] = kw.get('headers', {
            'Content-Type': 'application/json',
            'User-Agent': 'autocert',
        })
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

    def requests(self, method, paths=None, dests=None, jsons=None, product=True, **kw):
        if not paths or not hasattr(paths, '__iter__'):
            raise DestinationPathError(paths)
        if not dests or not hasattr(dests, '__iter__'):
            raise DestinationDestError(dests)
        if jsons:
            if len(jsons) != len(paths):
                raise JsonsDontMatchPathsError(jsons, paths)
            if product:
                kws = [self.keywords(path=path, dest=dest, json=json, **kw) for (path, json), dest in itertools.product(zip(paths, jsons), dests)]
            else:
                if len(dests) != len(paths):
                    raise DestsDontMatchPathsError(dests, paths)
                kws = [self.keywords(path=path, dest=dest, json=json, **kw) for (path, json), dest in zip(zip(paths, jsons), dests)]
        else:
            if product:
                kws = [self.keywords(path=path, dest=dest, **kw) for path, dest in itertools.product(paths, dests)]
            else:
                if len(dests) != len(paths):
                    raise DestsDontMatchPathsError(dests, paths)
                kws = [self.keywords(path=path, dest=dest, **kw) for path, dest in zip(paths, dests)]
        app.logger.debug('requests kws =')
        app.logger.debug(pformat(kws))
        return self.ar.requests(method, *kws)

    def gets(self, paths=None, dests=None, jsons=None, **kw):
        return self.requests('GET', paths=paths, dests=dests, jsons=jsons, **kw)

    def puts(self, paths=None, dests=None, jsons=None, **kw):
        return self.requests('PUT', paths=paths, dests=dests, jsons=jsons, **kw)

    def posts(self, paths=None, dests=None, jsons=None, **kw):
        return self.requests('POST', paths=paths, dests=dests, jsons=jsons, **kw)

    def deletes(self, paths=None, dests=None, jsons=None, **kw):
        return self.requests('DELETE', paths=paths, dests=dests, jsons=jsons, **kw)

    def has_connectivity(self, timeout, *dests):
        raise NotImplementedError

    def add_destinations(self, cert, *dests, **items):
        '''
        does this belong here?
        '''
        cert['destinations'] = cert.get('destinations', {})
        for dest in dests:
            cert['destinations'][dest] = items
        return cert

    def fetch_certificates(self, bundles, *dests):
        raise NotImplementedError

    def install_certificates(self, note, bundles, *dests):
        raise NotImplementedError

    def update_certificates(self, bundles, *dests):
        raise NotImplementedError

    def remove_certificates(self, bundles, *dests):
        raise NotImplementedError
