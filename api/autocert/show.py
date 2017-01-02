#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pprint, pformat
from attrdict import AttrDict
from fnmatch import fnmatch
from ruamel import yaml

from autocert import digicert
from autocert import zeus
from autocert import tar

from autocert.utils.dictionary import merge, head, body

def defaults(json):
    if not json:
        json = {}
    json['common_name_pattern'] = json.get('common_name_pattern', '*')
    json['authority_pattern'] = json.get('authority_pattern', '*')
    json['destination_pattern'] = json.get('destination_pattern', '*')
    return AttrDict(json)

def show(json=None):
    json = defaults(json)
    digicert_records = digicert.get_active_certificate_orders_and_details(json.common_name_pattern)
    records = []
    for record in digicert_records:
        record_name = head(record)
        record_body = body(record)
        print('record_name =', record_name)
        common_name = record_body['common_name']
        print('common_name =', common_name)
        installed = zeus.get_installed_certificates(json.destination_pattern, common_name)
        print('installed =', installed)
        zeus_record = {record_name: installed}
        print('zeus_record =', zeus_record)
        record = merge(record, zeus_record)
        print('record =', record)
        records += [record]
    return {'certs': records}
