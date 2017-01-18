#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import zipfile
from attrdict import AttrDict
from pprint import pprint, pformat
from fnmatch import fnmatch

from authority.base import AuthorityBase
from utils.dictionary import merge

from app import app

from config import CFG

def not_200(call):
    return call.recv.status != 200

class LetsEncryptAuthority(AuthorityBase):
    def __init__(self, ar, cfg, verbosity):
        super(LetsEncryptAuthority, self).__init__(ar, cfg, verbosity)

    def display(self, cert_name):
        raise NotImplementedError

    def renew_certificate(self, cert_name):
        raise NotImplementedError

    def revoke_certificate(self, cert_name):
        raise NotImplementedError
