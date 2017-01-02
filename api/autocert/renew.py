#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pformat

from autocert import digicert

def renew(json):
    return 'renew:\n{0}\n'.format(pformat(locals()))

