#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests

from flask import Flask, jsonify
from flask import request, render_template
from ruamel import yaml
from subprocess import check_output
from attrdict import AttrDict

from app.config import CFG

import logging
from logging.config import dictConfig

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

dictConfig(CFG.logging)
logger = logging.getLogger('auto-cert/api')
if 'LOG_LEVEL' in os.environ:
    el = logger.getEffectiveLevel()
    LOG_LEVEL = os.getenv('LOG_LEVEL')
    logger.log(el, 'environment variable found LOG_LEVEL="{0}"'.format(LOG_LEVEL))
    LOG_LEVEL = LOGGING_MAP[LOG_LEVEL]
    logger.log(el, 'environment variable found LOG_LEVEL="{0}"'.format(LOG_LEVEL))
    logger.setLevel(LOG_LEVEL)
    logger.log(el, 'LOG_LEVEL set to "{0}"'.format(LOG_LEVEL))


logger.info('starting api app')
app = Flask(__name__)

def is_valid_cert(status):
    return status not in INVALID_STATUS

@app.route('/version', methods=['GET'])
def version():
    logger.info('/version called')
    version = 'unknown'
    try:
        version = open(os.getcwd() + '/' + 'VERSION').read()
    except IOError:
        version = check_output('git describe', shell=True).decode('utf-8').strip()
    return jsonify({'version': version})

@app.route('/hello', methods=['GET'])
@app.route('/hello/<string:target>', methods=['GET'])
def hello(target='world'):
    logger.info('/hello called with target={target}'.format(**locals()))
    return jsonify({'msg': 'hello %(target)s' % locals()})

@app.route('/certs/list', methods=['GET'])
@app.route('/certs/list/<string:provider>', methods=['GET'])
def listcerts(provider='digicert'):
    logger.info('/certs/list called with provider={provider}'.format(**locals()))
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
