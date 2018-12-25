#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask
from logging.config import dictConfig

from config import CFG

dictConfig(CFG.logging)

app = Flask('api')
app.config['PROPAGATE_EXCEPTIONS'] = True
app.logger
