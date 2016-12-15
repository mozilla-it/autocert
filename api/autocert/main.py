#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import imp
import pwd
import sys

from flask import Flask, jsonify
from flask import request, render_template
from pdb import set_trace as breakpoint

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

