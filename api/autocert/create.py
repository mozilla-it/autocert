#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pformat

from autocert import digicert

def create(json):
    return 'create:\n{0}\n'.format(pformat(locals()))

