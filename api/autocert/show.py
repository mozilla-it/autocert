#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pprint, pformat
from attrdict import AttrDict
from fnmatch import fnmatch
from ruamel import yaml
from flask import jsonify

from autocert import digicert
from autocert import zeus
from autocert import tar

from autocert.utils.dictionary import merge, head, body

try:
    from autocert.app import app
except ImportError:
    from app import app

try:
    from autocert.config import CFG
except ImportError:
    from config import CFG

def defaults(json):
    if not json:
        json = {}
    json['common_name'] = json.get('common_name', '*')
    return AttrDict(json)

def show(json=None):
    json = defaults(json)
    digicert_records = digicert.get_active_certificate_orders_and_details(json.common_name)
    records = []
    for record in digicert_records:
        record_name = head(record)
        record_body = body(record)
        common_name = record_body['common_name']
        #installed = zeus.get_installed_certificates(json.destination, common_name)
        installed = zeus.get_installed_certificates(common_name, *list(CFG.destinations.zeus.keys()))
        zeus_record = {record_name: installed}
        record = merge(record, zeus_record)
        records += [record]
    return jsonify({'certs': records})
