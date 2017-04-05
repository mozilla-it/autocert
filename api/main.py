#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import imp
import pwd
import sys

from flask import Flask, request, jsonify, make_response
from pdb import set_trace as breakpoint

from pprint import pformat

from app import app

from endpoint.factory import create_endpoint
from utils.version import version as api_version
from utils.format import fmt
from utils.exceptions import AutocertError

app.config['PROPAGATE_EXCEPTIONS'] = True

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

@app.before_first_request
def initialize():
    from logging.config import dictConfig
    from config import CFG
    if sys.argv[0] != 'venv/bin/pytest':
        dictConfig(CFG.logging)     #3
        PID = os.getpid()
        PPID = os.getppid()
        USER = pwd.getpwuid(os.getuid())[0]
        app.logger.info('starting api with pid={PID}, ppid={PPID} by user={USER}'.format(**locals()))

def log_request(user, hostname, ip, method, path, json):
    app.logger.info(fmt('{user}@{hostname} from {ip} ran {method} {path} with json=\n"{json}"'))

@app.route('/autocert/version', methods=['GET'])
def version():
    args = request.json
    args = args if args else {}
    cfg = args.get('cfg', None)
    log_request(
        args.get('user', 'unknown'),
        args.get('hostname', 'unknown'),
        request.remote_addr,
        request.method,
        request.path,
        args)
    version = api_version()
    return jsonify({'version': api_version()})

@app.route('/autocert', methods=['GET', 'PUT', 'POST', 'DELETE'])
def route():
    args = request.json
    args = args if args else {}
    cfg = args.get('cfg', None)
    log_request(
        args.get('user', 'unknown'),
        args.get('hostname', 'unknown'),
        request.remote_addr,
        request.method,
        request.path,
        args)
    endpoint = create_endpoint(request.method, cfg, args)
    try:
        json, status = endpoint.execute()
    except AutocertError as ae:
        status = 500
        json = dict(errors={
            ae.name: ae.message
        })
    return make_response(jsonify(json), status)

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

if __name__ == '__main__':
    app.run()
