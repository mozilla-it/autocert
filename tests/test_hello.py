#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import inspect

from ruamel import yaml

from utils import docstr, jsonify
from main import app

def test_hello_default():
    '''
    expect:
        msg: hello world
    '''
    expect = yaml.load(docstr())['expect']
    client = app.test_client()
    client.testing = True
    result = client.get('/hello')
    actual = jsonify(result.get_data().decode('utf8'))
    assert expect == actual

def test_hello_param():
    '''
    expect:
        msg: hello auto-cert
    '''
    expect = yaml.load(docstr())['expect']
    client = app.test_client()
    client.testing = True
    result = client.get('/hello/auto-cert')
    actual = jsonify(result.get_data().decode('utf8'))
    assert expect == actual
