#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import inspect

from ruamel import yaml

from main import app
from utils import docstr, jsonify

def test_hello_default():
    '''
    expect:
        msg: hello world
    '''
    expect = yaml.load(docstr())['expect']
    client = app.test_client()
    client.testing = True
    result = client.get('/hello')
    assert result.status_code == 200
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
    assert result.status_code == 200
    actual = jsonify(result.get_data().decode('utf8'))
    assert expect == actual
