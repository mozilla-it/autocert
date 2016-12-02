#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pwd
import sys
import requests

from flask import Flask, jsonify
from flask import request, render_template
from ruamel import yaml
from subprocess import check_output
from attrdict import AttrDict

from app.config import CFG
from app.utils import version

#from flask_log import Logging


from pdb import set_trace as bp
from app.utils.version import version as api_version

from logging.config import dictConfig
from logging import (
    CRITICAL,
    ERROR,
    WARNING,
    INFO,
    DEBUG,
    NOTSET)

LOGGING_MAP = {
    'CRITICAL': CRITICAL,
    'ERROR':    ERROR,
    'WARNING':  WARNING,
    'INFO':     INFO,
    'DEBUG':    DEBUG,
    'NOTSET':   NOTSET,
}

INVALID_STATUS = [
    'expired',
    'rejected',
]

# the following statements have to be in THIS specfic order: 1, 2, 3
app = Flask('api')                  #1
app.logger                          #2

def log(*msgs):
    app.logger.log(app.logger.getEffectiveLevel(), ' '.join(msgs))


@app.before_first_request
def initialize():
    if sys.argv[0] != 'venv/bin/pytest':
        dictConfig(CFG.logging)     #3
        PID = os.getpid()
        PPID = os.getppid()
        USER = pwd.getpwuid(os.getuid())[0]
        app.logger.info('starting api with pid={PID}, ppid={PPID} by user={USER}'.format(**locals()))

def is_valid_cert(status):
    return status not in INVALID_STATUS

@app.route('/version', methods=['GET'])
def version():
    app.logger.info('/version called')
    version = api_version()
    return jsonify({'version': version})

@app.route('/hello', methods=['GET'])
@app.route('/hello/<string:target>', methods=['GET'])
def hello(target='world'):
    app.logger.info('/hello called with target={target}'.format(**locals()))
    return jsonify({'msg': 'hello %(target)s' % locals()})

@app.route('/certs/list', methods=['GET'])
@app.route('/certs/list/<string:provider>', methods=['GET'])
def listcerts(provider='digicert'):
    app.logger.info('/certs/list called with provider={provider}'.format(**locals()))
    if provider == 'digicert':
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'auto-cert',
        }
        response = requests.get(
            CFG.providers.digicert.baseurl / 'order/certificate',
            auth=CFG.providers.digicert.auth,
            headers=headers)
        if response.status_code == 200:
            obj = AttrDict(response.json())
            count = len(obj.orders)
            certs = [ cert for cert in obj.orders if is_valid_cert(cert.status) ]
            return jsonify(certs=certs)
        else:
            app.logger.error('failed request to /certs/list with status_code={0}'.format(response.status_code))
