#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.config: provides CFG for cli code
'''

import os
from ruamel import yaml
from attrdict import AttrDict
from cli.utils.dictionary import merge

CFG_FILES = [
    '{0}/autocert.yml'.format(os.path.dirname(__file__)),
    '~/.config/autocert/autocert.yml',
]

def _load_config(cfgs):
    config = {}
    for cfg in cfgs:
        if os.path.isfile(cfg):
            with open(cfg, 'r') as f:
                yml = yaml.safe_load(f)
                if yml:
                    config = merge(config, yml)
    return AttrDict(config)

CFG = _load_config(CFG_FILES)
