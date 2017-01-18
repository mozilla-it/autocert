#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
output
'''

try:
    from ruamel import yaml
    from urlpath import URL
    from attrdict import AttrDict
    from packaging.version import parse as version_parse
except ImportError as ie:
    print(ie)
    print('perhaps you need to install cli/requirements.txt via pip3')


def str_presenter(dumper, data):
    str_tag = 'tag:yaml.org,2002:str'
    if len(data.splitlines()) > 1:
        return dumper.represent_scalar(str_tag, data, style='|')
    return dumper.represent_scalar(str_tag, data)

yaml.add_representer(str, str_presenter)

def list_presenter(dumper, data):
    list_tag = 'tag:yaml.org,2002:seq'
    if len(data) > 1:
        if all([isinstance(item, str) for item in data]):
            return dumper.represent_sequence(list_tag, data, flow_style=False)
    return dumper.represent_sequence(list_tag, data)

yaml.add_representer(list, list_presenter)

def yaml_format(obj):
    class MyDumper(yaml.Dumper):
        def represent_mapping(self, tag, mapping, flow_style=False):
            return yaml.Dumper.represent_mapping(self, tag, mapping, flow_style)
    return yaml.dump(obj, Dumper=MyDumper).strip()

def output(obj):
    return print(yaml_format(obj))

