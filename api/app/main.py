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

import logging
from logging.config import dictConfig
from logging.handlers import RotatingFileHandler

from pdb import set_trace as bp
from app.utils.version import version as api_version

LOGGING_MAP = {
    'CRITICAL': logging.CRITICAL,
    'ERROR':    logging.ERROR,
    'WARNING':  logging.WARNING,
    'INFO':     logging.INFO,
    'DEBUG':    logging.DEBUG,
    'NOTSET':   logging.NOTSET,
}

INVALID_STATUS = [
    'expired',
    'rejected',
]

# the following statements have to be in THIS specfic order: 1, 2, 3
app = Flask('api')                  #1
app.logger                          #2

def logit(msg):
    app.logger.log(app.logger.getEffectiveLevel(), msg)


@app.before_first_request
def initialize():
    if sys.argv[0] != 'venv/bin/pytest':
        dictConfig(CFG.logging)     #3

        logit(dir(app.logger.handlers[1]))

        logit('sys.argv = '+' '.join(sys.argv))
        logit('1 app.logger.handlers = '+ ' '.join([handler.name for handler in app.logger.handlers]))

        PID = os.getpid()
        PPID = os.getppid()
        USER = pwd.getpwuid(os.getuid())[0]
        logit('starting api with pid={PID}, ppid={PPID} by user={USER}'.format(**locals()))
        LOG_LEVEL = os.getenv('LOG_LEVEL', None)
        logit('LOG_LEVEL={LOG_LEVEL}'.format(**locals()))
        if LOG_LEVEL in LOGGING_MAP:
            LOG_VALUE = LOGGING_MAP[LOG_LEVEL]
            logit('LOG_VALUE={LOG_VALUE}'.format(**locals()))
            app.logger.setLevel(LOG_VALUE)
            for handler in app.logger.handlers:
                logit('hander .name = {0}'.format(handler.name))
                handler.setLevel(LOG_VALUE)
            logit('log level set to {LOG_LEVEL}({LOG_VALUE})'.format(**locals()))

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
    logit('2 app.logger.handlers = '+ ' '.join([handler.name for handler in app.logger.handlers]))
    app.logger.info('/certs/list called with provider={provider}'.format(**locals()))
    app.logger.log(app.logger.getEffectiveLevel(), 'LISTCERTS YO!')
    if provider == 'digicert':
        headers = {
            'X-DC-DEVKEY': CFG.providers.digicert.apikey,
            'Accept': 'application/json',
        }
        url = 'https://www.digicert.com/services/v2/order/certificate'
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            obj = AttrDict(response.json())
            count = len(obj.orders)
            certs = [ cert for cert in obj.orders if is_valid_cert(cert.status) ]
            return jsonify(certs=certs)
        else:
            logging.error('failed request to /certs/list with status_code={0}'.format(response.status_code))

#if __name__ == '__main__':
#    bp()
#    print('WOAH!')
