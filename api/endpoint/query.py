#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

from attrdict import AttrDict
from fnmatch import fnmatch
from ruamel import yaml

from utils.dictionary import merge, head, head_body
from utils.format import fmt, pfmt
from app import app
from config import CFG
from endpoint.base import EndpointBase
from utils.output import yaml_format

from utils import sift

class QueryEndpoint(EndpointBase):
    def __init__(self, cfg, args):
        super(QueryEndpoint, self).__init__(cfg, args)

    def execute(self, **kwargs):
        if self.args.target == 'digicert':
            return self.query_digicert(**kwargs)
        return dict(query='results'), 200

    def filter(self, order):
        if not sift.fnmatches(order.certificate.get('dns_names', []), self.args.domain_name_pns):
            print('filter: return False')
            return False
        if not sift.fnmatches([order.status], self.args.status):
            print('filter: return False')
            return False
        print('filter: return True')
        return True

    def query_digicert(self, **kwargs):
        call = self.authorities.digicert._get_certificate_order_summary()
        results = AttrDict(call.recv.json)
        summaries = [dict(order) for order in results.orders if self.filter(order)]
        if self.args.result_detail == 'summary':
            return dict(results=summaries), call.recv.status
        order_ids = [summary['id'] for summary in summaries]
        calls = self.authorities.digicert._get_certificate_order_detail(order_ids)
        details = [call.recv.json for call in calls]
        return dict(results=details), 200
