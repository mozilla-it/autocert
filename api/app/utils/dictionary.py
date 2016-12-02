#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def dict_to_attrs(obj, d):
    for k, v in d.items():
        setattr(obj, k, v)
    return obj

def update(d1, d2):
    d1.update(d2)
    return d1

