#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from utils.fmt import fmt

def utcnow():
    return datetime.utcnow()

def datetime2int(dt, pattern='%Y%m%d%H%M%S'):
    return int(dt.strftime(pattern))

def int2datetime(i, pattern='%Y%m%d%H%M%S'):
    return datetime.strptime(fmt('{i}'), pattern)

def string2datetime(s, pattern='%Y-%m-%d'):
    return datetime.strptime(s, pattern)

def string2int(s, pattern='%Y-%m-%d'):
    return datetime2int(string2datetime(s, pattern=pattern))
