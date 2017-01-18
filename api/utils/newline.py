#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def windows2unix(string):
    return string.replace('\r\n', '\n')

def unix2windows(string):
    return string.replace('\n', '\r\n')

