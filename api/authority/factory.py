#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
authority.factory
'''

from utils.format import fmt

from app import app

from authority.digicert import DigicertAuthority
from authority.letsencrypt import LetsEncryptAuthority

def create_authority(authority, ar, cfg, verbosity):
    if authority == 'digicert':
        return DigicertAuthority(ar, cfg, verbosity)
    elif authority == 'letsencrypt':
        return LetsEncryptAuthority(ar, cfg, verbosity)
    return None #FIXME should be error
