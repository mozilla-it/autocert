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
        if sift.fnmatches(order.certificate.dns_names, self.args.domain_name_pns):
            return True
        return False

    def query_digicert(self, **kwargs):
        call = self.authorities.digicert._get_certificate_order_summary()
        results = AttrDict(call.recv.json)
        summaries = [dict(order) for order in results.orders if self.filter(order)]
        if self.args.result_detail == 'summary':
            return dict(results=summaries), call.recv.status
        return dict(foo='bar'), 200
