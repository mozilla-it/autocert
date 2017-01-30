#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
destination.factory
'''

from app import app

from destination.aws import AwsDestination
from destination.zeus import ZeusDestination

def create_destination(destination, ar, cfg, verbosity):
    if destination == 'aws':
        return AwsDestination(ar, cfg, verbosity)
    elif destination == 'zeus':
        return ZeusDestination(ar, cfg, verbosity)
    return None #FIXME should be error

