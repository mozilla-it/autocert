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
    args = defaults(json)
    digicert_records = digicert.get_active_certificate_orders_and_details(args.common_name)
    records = []
    for record in digicert_records:
        record_name = head(record)
        record_body = body(record)
        csr = record_body['authorities']['digicert']['csr']
        common_name = record_body['common_name']
        installed = zeus.get_installed_certificates(csr, common_name, *list(CFG.destinations.zeus.keys()))
        zeus_record = {record_name: installed.get(common_name, {})}
        record = merge(record, zeus_record)
        tar_record = tar.get_records_from_tarfiles(record_name)
        record = merge(record, tar_record)
        records += [record]
    return jsonify({'certs': records})
