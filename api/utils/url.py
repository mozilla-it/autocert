#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
url
'''
import socket

from urlpath import URL
from utils.fmt import fmt
from utils.exceptions import AutocertError

class UrlDnsError(AutocertError):
    def __init__(self, url, errors=None):
        msg = fmt('url dns resoltuion with {url}')
        super(UrlDnsError, self).__init__(msg)

class UrlConnectError(AutocertError):
    def __init__(self, url, errors=None):
        msg = fmt('url connect error {url}')
        super(UrlConnectError, self).__init__(msg)

def validate(url, throw=False):
    if not isinstance(url, URL):
        url = URL(url)
    proto = url.components[0]
    hostname = url.hostname
    try:
        address = socket.gethostbyname(hostname)
    except Exception as ex:
        if throw:
            raise UrlDnsError(url, errors=[ex])
        return False
    try:
        family, socktype, proto, _, address = socket.getaddrinfo(address, proto)[0]
        s = socket.socket(family, socktype, proto)
        s.connect(address)
    except Exception as ex:
        if throw:
            raise UrlConnectError(url, errors=[ex])
        return False
    return True
