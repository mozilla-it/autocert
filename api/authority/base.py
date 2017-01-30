#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
authority.base
'''
from attrdict import AttrDict
from pprint import pprint

from utils.format import fmt

class AuthorityFactoryError(Exception):
    def __init__(self, authority):
        msg = fmt('authority factory error {authority}')
        super(AuthorityFactoryError, self).__init__(msg)

class AuthorityPathNotSetError(Exception):
    def __init__(self):
        msg = 'authority path not set'
        super(AuthorityPathNotSetError, self).__init__(msg)

class AuthorityBase(object):
    def __init__(self, ar, cfg, verbosity):
        self.ar = ar
        self.cfg = AttrDict(cfg)
        self.verbosity = verbosity

    def keywords(self, path=None, **kw):
        if not path:
            raise AuthorityPathNotSetError
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

    def requests(self, method, *kws):
        kws = [self.keywords(**kw) for kw in kws]
        return self.ar.requests(method, *kws)

    def gets(self, *kws):
        return self.requests('GET', *kws)

    def puts(self, *kws):
        return self.requests('PUT', *kws)

    def posts(self, *kws):
        return self.requests('POST', *kws)

    def deletes(self, *kws):
        return self.requests('DELETE', *kws)

    def display_certificates(self, certs):
        raise NotImplementedError

    def create_certificate(self, common_name, sans=None):
        raise NotImplementedError

    def renew_certificates(self, certs):
        raise NotImplementedError

    def revoke_certificates(self, certs):
        raise NotImplementedError

