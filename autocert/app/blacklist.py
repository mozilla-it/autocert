#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from exceptions import AutocertError
from utils.fmt import *
from utils import sift

try:
    thisdir = os.path.dirname(os.path.abspath(__file__))
    items = open(fmt('{thisdir}/BLACKLIST')).read().strip().split()
    BLACKLIST = [item for item in items if not item.startswith('#')]
except Exception as ex:
    print('error happened when loading the BLACKLIST')
    print(ex)
    BLACKLIST = ['']

class BlacklistError(AutocertError):
    def __init__(self, names):
        msg = fmt('these certs caused a blacklist error: {names}')
        super(BlacklistError, self).__init__(msg)

def check(certs, overrides):
    print('blacklist.check: overrides =', overrides)
    blacklist_names = []
    for cert in certs:
        domains = [cert.common_name] + (cert.sans if cert.sans else [])
        print('domains =', domains)
        blacklist_names += sift.fnmatches(domains, BLACKLIST, overrides)
    if blacklist_names:
        raise BlacklistError(blacklist_names)
