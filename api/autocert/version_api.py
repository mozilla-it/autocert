#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify
api = Blueprint('version_api', __name__)

from autocert.utils.version import version as api_version

@api.route('/version', methods=['GET'])
def version():
    from flask import current_app
    current_app.logger.info('/version called')
    version = api_version()
    return jsonify({'version': version})

