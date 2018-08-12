#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

from attrdict import AttrDict
from fnmatch import fnmatch
from ruamel import yaml
from datetime import datetime, timedelta

from utils.dictionary import merge, head, head_body
from utils.fmt import fmt, pfmt
from app import app
from config import CFG
from endpoint.base import EndpointBase
from utils.yaml import yaml_format

from utils import sift

import traceback

TIMEDELTA_ZERO = timedelta(0)

class QueryEndpoint(EndpointBase):
    def __init__(self, cfg, args):
        super(QueryEndpoint, self).__init__(cfg, args)

    def execute(self, **kwargs):
        if self.args.target == 'digicert':
            return self.query_digicert(**kwargs)
        return dict(query='results'), 200

    def filter(self, order):
        try:
            status = order['status']
            certificate = order['certificate']
            common_name = certificate.get('common_name', 'UNDEF')
            dns_names = certificate.get('dns_names', [])
            valid_till = certificate['valid_till']
            if sift.fnmatches(dns_names, self.args.domain_name_pns):
                if sift.fnmatches([status], self.args.status):
                    if isinstance(self.args.within, int):
                        within = timedelta(self.args.within)
                        delta = datetime.strptime(valid_till, '%Y-%m-%d') - datetime.utcnow()
                        return TIMEDELTA_ZERO < delta and delta < within
                    return True
        except Exception as ex:
            app.logger.debug('FILTER_EX: ' + traceback.format_exc())
        return False

    def query_digicert(self, **kwargs):
        call = self.authorities.digicert._get_certificate_order_summary()
        def orders(call): #FIXME: ugly hack to compile all orders from 'prev' linked list structure
            if call:
                return call.recv.json.orders + orders(call.get('prev', None))
            return []
        results = [dict(order) for order in orders(call) if self.filter(order)]
        if self.args.result_detail == 'detailed':
            order_ids = [result['id'] for result in results]
            calls = self.authorities.digicert._get_certificate_order_detail(order_ids)
            results = [call.recv.json for call in calls]
        return dict(count=len(results), results=results), 200
