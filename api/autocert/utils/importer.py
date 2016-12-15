#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import imp

def import_modules(dirpath, endswith):
    files = [f for f in os.listdir(dirpath) if f.endswith(endswith)]
    return [imp.load_source(f.split('.')[0], dirpath+'/'+f) for f in files]
