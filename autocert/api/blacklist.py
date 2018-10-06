#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from exceptions import AutocertError
from utils import sift
from utils.fmt import *

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
        msg = fmt('these bundles caused a blacklist error: {names}')
        super(BlacklistError, self).__init__(msg)

def check(bundles, overrides):
    print('blacklist.check: overrides =', overrides)
    blacklist_names = []
    for bundle in bundles:
        domains = [bundle.common_name] + (bundle.sans if bundle.sans else [])
        print('domains =', domains)
        blacklist_names += sift.fnmatches(domains, BLACKLIST, overrides)
    if blacklist_names:
        raise BlacklistError(blacklist_names)
