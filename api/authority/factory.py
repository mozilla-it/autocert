#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
authority.factory
'''

from utils.format import fmt

from app import app

from authority.digicert import DigicertAuthority
from authority.letsencrypt import LetsEncryptAuthority

def create_authority(authority, cfg, verbosity):
    app.logger.debug('create_auhtority:\n{0}', locals())
    if authority == 'digicert':
        return DigicertAuthority(cfg, verbosity)
    elif authority == 'letsencrypt':
        return LetsEncryptAuthority(cfg, verbosity)
    return None #FIXME should be error
