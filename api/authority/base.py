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

    def request(self, method, path=None, **kw):
        if not path:
            raise AuthorityPathNotSetError
        url = str(self.cfg.baseurl / path)
        auth = kw.pop('auth', self.cfg.auth)
        headers = kw.pop('headers', self.cfg.headers)
        print(fmt('AuthorityBase.request: method={method} path={path}\n{kw}'))
        return self.ar.request(method, url=url, auth=auth, headers=headers, **kw)

    def get(self, path=None, **kw):
        return self.request('GET', path=path, **kw)

    def put(self, path=None, **kw):
        return self.request('PUT', path=path, **kw)

    def post(self, path=None, **kw):
        return self.request('POST', path=path, **kw)

    def delete(self, path=None, **kw):
        return self.request('DELETE', path=path, **kw)

    def display_certificate(self, cert_name):
        raise NotImplementedError

    def create_certificate(self, common_name, sans=None):
        raise NotImplementedError

    def renew_certificate(self, cert_name):
        raise NotImplementedError

    def revoke_certificate(self, cert_name):
        raise NotImplementedError

