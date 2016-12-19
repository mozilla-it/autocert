#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import imp
import pwd
import sys

from flask import Flask, jsonify
from flask import request, render_template
from pdb import set_trace as breakpoint

STATUS_CODES = {
    400: 'bad request',
    401: 'unauthorized',
    402: 'payment required',
    403: 'forbidden',
    404: 'not found',
    405: 'method not allowed',
    406: 'not acceptable',
    407: 'proxy authentication required',
    408: 'request timed-out',
    409: 'conflict',
    410: 'gone',
    411: 'length required',
    412: 'precondition failed',
    413: 'payload too large',
    414: 'uri too long',
    415: 'unsupported media type',
    416: 'range not satisfiable',
    417: 'expectation failed',
    418: 'im a teapot',
    421: 'misdirected request',
    422: 'unprocessable entity',
    423: 'locked',
    424: 'failed dependency',
    426: 'upgrade required',
    428: 'precondition required',
    429: 'too many requires',
    431: 'request header fields too large',
    451: 'unavailable for legal reasons',

    500: 'internal server error',
    501: 'not implemented',
    502: 'bad gateway',
    503: 'service unavailable',
    504: 'gateway timed out',
    505: 'http version not supported',
    506: 'variant also negotiates',
    507: 'insufficient storage',
    508: 'loop detected',
    510: 'not extended',
    511: 'network authentication required',
}

# the following statements have to be in THIS specfic order: 1, 2, 3
app = Flask('api')                  #1
app.logger                          #2

app.config['PROPAGATE_EXCEPTIONS'] = True

def register_apis():
    from autocert.utils.importer import import_modules
    dirpath = os.path.dirname(__file__)
    endswith = '_api.py'
    [app.register_blueprint(mod.api) for mod in import_modules(dirpath, endswith)]

register_apis()

@app.before_first_request
def initialize():
    from logging.config import dictConfig
    from autocert.config import CFG
    if sys.argv[0] != 'venv/bin/pytest':
        dictConfig(CFG.logging)     #3
        PID = os.getpid()
        PPID = os.getppid()
        USER = pwd.getpwuid(os.getuid())[0]
        app.logger.info('starting api with pid={PID}, ppid={PPID} by user={USER}'.format(**locals()))

def log_and_jsonify_error(status, error, request):
    message = STATUS_CODES[status]
    request_path = request.path
    app.logger.error('{message}: {request_path}'.format(**locals()))
    return jsonify({
        'errors': [
            '{status}: {message}, {request_path}'.format(**locals()),
        ],
    })

@app.errorhandler(400)
def bad_request(error):
    return log_and_jsonify_error(400, error, request)

@app.errorhandler(401)
def unauthorized(error):
    return log_and_jsonify_error(401, error, request)

@app.errorhandler(403)
def page_not_found(error):
    return log_and_jsonify_error(403, error, request)

@app.errorhandler(404)
def page_not_found(error):
    return log_and_jsonify_error(404, error, request)

@app.errorhandler(405)
def method_not_allowed(error):
    return log_and_jsonify_error(405, error, request)


@app.errorhandler(500)
def internal_server_error(error):
    return log_jsonify_error(500, error, request)

@app.errorhandler(503)
def service_unavailable(error):
    return log_jsonify_error(503, error, request)


@app.errorhandler(Exception)
def unhandled_exception(ex):
    app.logger.error('unhandled exception', exc_info=True)
