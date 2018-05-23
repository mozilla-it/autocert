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
        if sift.fnmatches(order['certificate'].get('dns_names', []), self.args.domain_name_pns):
            app.logger.info(fmt('order_status={0} args_status={1}', order['status'], self.args.status))
            if sift.fnmatches([order['status']], self.args.status):
                return True
        return False

    def query_digicert(self, **kwargs):
        call = self.authorities.digicert._get_certificate_order_summary()
        results = [dict(order) for order in call.recv.json['orders'] if self.filter(order)]
        if self.args.result_detail == 'detailed':
            order_ids = [result['id'] for result in results]
            calls = self.authorities.digicert._get_certificate_order_detail(order_ids)
            results = [call.recv.json for call in calls]
        return dict(results=results), 200
