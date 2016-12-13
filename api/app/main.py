#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pwd
import sys
import requests

from fnmatch import fnmatch

from flask import Flask, jsonify
from flask import request, render_template
from ruamel import yaml
from subprocess import check_output
from attrdict import AttrDict

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

from app.config import CFG
from app.utils import version
from app.utils.dictionary import merge

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

def digicert_list_certs():
    app.logger.info('digicert_list_certs called')
    response = requests.get(
        CFG.authorities.digicert.baseurl / 'order/certificate',
        auth=CFG.authorities.digicert.auth,
        headers=CFG.authorities.digicert.headers)
    if response.status_code == 200:
        from pprint import pformat
        obj = AttrDict(response.json())
        app.logger.debug('digicert_list_certs: obj.orders="{0}"'.format(pformat(obj.orders)))
        certs = [ cert for cert in obj.orders if is_valid_cert(cert.status) ]
        app.logger.debug('digicert_list_certs: certs="{0}"'.format(pformat(certs)))
        return {
            'certs': list(certs),
        }
    else:
        app.logger.error('failed request to /list/certs with status_code={0}'.format(response.status_code))

def letsencrypt_list_certs():
    app.logger.info('letsencrypt_list_certs called')
    return {
        'certs': []
    }

AUTHORITIES = {
    'digicert': digicert_list_certs,
    'letsencrypt': letsencrypt_list_certs,
}

@app.route('/list/certs', methods=['GET'])
@app.route('/list/certs/<string:pattern>', methods=['GET'])
def list_certs(pattern='*'):
    app.logger.info('/list/certs called with pattern="{pattern}"'.format(**locals()))
    authorities = [authority for authority in AUTHORITIES.keys() if fnmatch(authority, pattern)]
    app.logger.debug('authorities="{authorities}"'.format(**locals()))
    funcs = [AUTHORITIES[authority] for authority in authorities]
    results = [func() for func in funcs]
    app.logger.debug('len(results)={0}'.format(len(results)))
    for result in results:
        app.logger.debug('1) len(result["certs"])="{0}"'.format(len(result['certs'])))
    result = merge(*results)
    app.logger.debug('2) len(result["certs"])="{0}"'.format(len(result['certs'])))
    return jsonify(result)
