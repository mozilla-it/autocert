#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pformat

from autocert import digicert

def revoke(json):
    return 'revoke:\n{0}\n'.format(pformat(locals()))
