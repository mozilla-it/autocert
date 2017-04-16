#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
authority.base
'''

from itertools import product
from attrdict import AttrDict

from utils.format import fmt
from utils.exceptions import AutocertError

from app import app

class AuthorityFactoryError(AutocertError):
    def __init__(self, authority):
        message = fmt('authority factory error {authority}')
        super(AuthorityFactoryError, self).__init__(message)

class AuthorityPathError(AutocertError):
    def __init__(self, path_or_paths):
        message = fmt('error with AuthorityBase param path(s) = {path_or_paths}')
        super(AuthorityPathError, self).__init__(message)

class JsonsDontMatchPathsError(AutocertError):
    def __init__(self, jsons, paths):
        len_jsons = len(jsons) if isinstance(jsons, list) else None
        len_paths = len(paths) if isinstance(paths, list) else None
        message = fmt('len(jsons) -> {len_jsons} != len(paths) -> {len_paths}; jsons={jsons}, paths={paths}')
        super(JsonsDontMatchPathsError, self).__init__(message)

class AuthorityBase(object):
    def __init__(self, ar, cfg, verbosity):
        self.ar = ar
        self.cfg = AttrDict(cfg)
        self.verbosity = verbosity

    def keywords(self, path=None, **kw):
        if not path:
            raise AuthorityPathError(path)
        kw['url'] = str(self.cfg.baseurl / path)
        kw['auth'] = kw.get('auth', self.cfg.auth)
        kw['headers'] = kw.get('headers', self.cfg.headers)
        return kw

    def request(self, method, **kw):
        return self.ar.request(method, **self.keywords(**kw))

    def get(self, path=None, **kw):
        return self.request('GET', path=path, **kw)

    def put(self, path=None, **kw):
        return self.request('PUT', path=path, **kw)

    def post(self, path=None, **kw):
        return self.request('POST', path=path, **kw)

    def delete(self, path=None, **kw):
        return self.request('DELETE', path=path, **kw)

    def requests(self, method, paths=None, jsons=None, **kw):
        if not paths or not hasattr(paths, '__iter__'):
            raise AuthorityPathError(paths)
        if jsons:
            if len(jsons) != len(paths):
                raise JsonsDontMatchPathsError(jsons, paths)
            kws = [self.keywords(path=path, json=json, **kw) for (path, json) in product(paths, jsons)]
        else:
            kws = [self.keywords(path=path, **kw) for path in paths]
        return self.ar.requests(method, *kws)

    def gets(self, paths=None, jsons=None, **kw):
        return self.requests('GET', paths=paths, jsons=jsons, **kw)

    def puts(self, paths=None, jsons=None, **kw):
        return self.requests('PUT', paths=paths, jsons=jsons, **kw)

    def posts(self, paths=None, jsons=None, **kw):
        return self.requests('POST', paths=paths, jsons=jsons, **kw)

    def deletes(self, paths=None, jsons=None, **kw):
        return self.requests('DELETE', paths=paths, jsons=jsons, **kw)

    def display_certificates(self, certs):
        raise NotImplementedError

    def create_certificate(self, organization_name, common_name, validity_years, csr, sans=None, repeat_delta=None):
        raise NotImplementedError

    def renew_certificates(self, certs, validity_years, repeat_delta=None):
        raise NotImplementedError

    def revoke_certificates(self, certs):
        raise NotImplementedError

