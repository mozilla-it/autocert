#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask
app = Flask('api')
app.config['PROPAGATE_EXCEPTIONS'] = True
app.logger
