#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
authority.factory
'''

from app.utils.fmt import *
from app.exceptions import AutocertError
from app.authority.digicert import DigicertAuthority
from app.authority.letsencrypt import LetsEncryptAuthority
from app.app import app

class AuthorityFactoryError(AutocertError):
    def __init__(self, authority):
        msg = fmt('authority factory error with {authority}')
        super(AuthorityFactoryError, self).__init__(msg)

def create_authority(authority, ar, cfg, verbosity):
    a = None
    if authority == 'digicert':
        return DigicertAuthority(ar, cfg, verbosity)
    elif authority == 'letsencrypt':
        return LetsEncryptAuthority(ar, cfg, verbosity)
    else:
        raise AuthorityFactoryError(authority)
    if a.has_connectivity():
        return a
