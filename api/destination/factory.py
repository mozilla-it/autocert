#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
destination.factory
'''

from utils.format import fmt

try:
    from autocert.app import app
except ImportError:
    from app import app

from destination.aws import AwsDestination
from destination.zeus import ZeusDestination

def create_destination(destination, cfg, verbosity):
    app.logger.debug('create_destination:\n{0}', locals())
    if destination == 'aws':
        return AwsDestination(cfg, verbosity)
    elif destination == 'zeus':
        return ZeusDestination(cfg, verbosity)
    return None #FIXME should be error

