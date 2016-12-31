#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pformat

from autocert import digicert
from autocert.utils.version import version as api_version

def version():
    return {'version': api_version()}



def show(common_name, json=None):
    r, orders = digicert.get('order/certificate')
    return 'show:\n{0}\n'.format(pformat(locals()))

def renew(common_name, json):
    return 'renew:\n{0}\n'.format(pformat(locals()))

def create(common_name, json):
    return 'create:\n{0}\n'.format(pformat(locals()))

def revoke(common_name, json):
    return 'revoke:\n{0}\n'.format(pformat(locals()))

