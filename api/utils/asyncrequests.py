#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import aiohttp
import asyncio

from json import dumps as json_dumps
from pprint import pprint, pformat
from attrdict import AttrDict
from datetime import datetime

from utils.newline import windows2unix
from utils.dictionary import merge

class RaiseIfError(Exception):
    def __init__(self, call):
        msg = 'raise if error with {0}'.format(call)
        super(RaiseIfError, self).__init__(msg)

class AsyncRequests(object):
    def __init__(self, verbosity, config):
        self._loop = asyncio.get_event_loop()
        self.calls = []
        self.verbosity = verbosity
        self.config = config
        self.auth = config.auth
        self.headers = config.headers

    @property
    def call(self):
        if self.calls:
            return self.calls[-1]
        return None

    async def _request(self, method, path=None, json=None, raise_if=None, raise_ex=None, repeat_if=None, repeat_wait=3, repeat_delta=None):
        start = datetime.now()
        url = str(self.config.baseurl / path)
        async with aiohttp.ClientSession(loop=self._loop) as session:
            repeat = 0
            while True:
                send_datetime = datetime.utcnow()
                async with session.request(
                    method,
                    url,
                    headers=self.headers,
                    auth=aiohttp.helpers.BasicAuth(*self.auth),
                    data=json_dumps(json) if json else None) as response:

                    text = await response.text()
                    recv_datetime = datetime.utcnow()
                    send = AttrDict(
                        method=method,
                        url=url,
                        json=json,
                        headers=self.headers,
                        datetime=send_datetime)
                    call = {}
                    json = None
                    if response.headers['Content-Type'] == 'application/json':
                        json = await response.json()
                        if json:
                            call = json
                    recv = AttrDict(
                        response=response,
                        headers=dict(response.headers.items()),
                        status=response.status,
                        text=windows2unix(text),
                        json=json,
                        repeat=repeat,
                        datetime=datetime.utcnow())
                    call = AttrDict(merge(call, dict(
                        send=send,
                        recv=recv)))
                self.calls += [call]
                if repeat_if and repeat_if(call):
                    delta = datetime.now() - start
                    if repeat_delta and delta < repeat_delta:
                        repeat += 1
                        await asyncio.sleep(repeat_wait)
                        continue
                if raise_if and raise_if(call):
                    if raise_ex:
                        raise raise_ex(call)
                    raise RaiseIfError(call)
                break
        return call

    def request(self, method, **kw):
        return self._loop.run_until_complete(self._request(method, **kw))

    def get(self, **kw):
        return self.request('GET', **kw)

    def put(self, **kw):
        return self.request('PUT', **kw)

    def post(self, **kw):
        return self.request('POST', **kw)

    def delete(self, **kw):
        return self.request('DELETE', **kw)

    async def _requests(self, method, *kws):
        futures = [asyncio.ensure_future(self._request(method, **kw)) for kw in kws]
        responses = await asyncio.gather(*futures)
        return responses

    def requests(self, method, *kws):
        future = asyncio.ensure_future(self._requests(method, *kws))
        return self._loop.run_until_complete(future)

    def gets(self, *kws):
        return self.requests('GET', *kws)

    def puts(self, *kws):
        return self.requests('PUT', *kws)

    def posts(self, *kws):
        return self.requests('POST', *kws)

    def deletes(self, *kws):
        return self.requests('DELETE', *kws)

