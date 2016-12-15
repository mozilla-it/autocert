#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from flask import Blueprint, jsonify
api = Blueprint('hello_api', __name__)

@api.route('/hello', methods=['GET'])
@api.route('/hello/<string:target>', methods=['GET'])
def hello(target='world'):
    from flask import current_app
    current_app.logger.info('/hello called with target={target}'.format(**locals()))
    return jsonify({'msg': 'hello %(target)s' % locals()})
