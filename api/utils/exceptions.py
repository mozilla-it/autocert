#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class AutocertError(Exception):
    def __init__(self, message):
        self._message = message
        super(AutocertError, self).__init__(message)

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def message(self):
        return self._message
