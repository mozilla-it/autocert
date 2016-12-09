#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.output
'''

try:
    from ruamel import yaml
    from urlpath import URL
    from attrdict import AttrDict
    from packaging.version import parse as version_parse
except ImportError as ie:
    print(ie)
    print('perhaps you need to install cli/requirements.txt via pip3')

def yaml_format(obj):
    class MyDumper(yaml.Dumper):
        def represent_mapping(self, tag, mapping, flow_style=False):
            return yaml.Dumper.represent_mapping(self, tag, mapping, flow_style)
    return yaml.dump(obj, Dumper=MyDumper).strip()

def output(obj):
    return print(yaml_format(obj))

