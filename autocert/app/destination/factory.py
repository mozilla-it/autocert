#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
destination.factory
'''

from app.config import CFG
from app.utils.fmt import *
from app.exceptions import AutocertError
from app.destination.aws import AwsDestination
from app.destination.zeus import ZeusDestination
from app.app import app

class DestinationFactoryError(AutocertError):
    def __init__(self, destination):
        msg = fmt('destination factory error with {destination}')
        super(DestinationFactoryError, self).__init__(msg)

def create_destination(destination, ar, cfg, timeout, verbosity):
    d = None
    if destination == 'aws':
        d = AwsDestination(ar, cfg, verbosity)
    elif destination == 'zeus':
        d = ZeusDestination(ar, cfg, verbosity)
    else:
        raise DestinationFactoryError(destination)
    dests = list(CFG.destinations.zeus.keys())
    if d.has_connectivity(timeout, *dests):
        return d

