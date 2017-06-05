#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from utils import sift
from utils.format import fmt

from utils.exceptions import AutocertError

try:
    BLACKLIST = [item for item in open('../BLACKLIST').read().strip().split() if not item.startswith('#')]
except:
    BLACKLIST = ['']

class BlacklistError(AutocertError):
    def __init__(self, names):
        msg = fmt('these certs caused a blacklist error: {names}')
        super(BlacklistError, self).__init__(msg)

def check(certs):
    blacklist_names = []
    for cert in certs:
        if sift.fnmatches(cert.common_name, BLACKLIST):
            blacklist_names += [cert.common_name]
        if cert.sans:
            for san in cert.sans:
                if sift.fnmatches(san, BLACKLIST):
                    blacklist_names += [san]
    if blacklist_names:
        raise BlacklistError(blacklist_names)
