#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import aiohttp
import asyncio


from json import dumps as json_dumps
from pprint import pprint, pformat
from attrdict import AttrDict
from datetime import datetime

from utils.format import fmt, pfmt
from utils.newline import windows2unix
from utils.dictionary import merge
from utils.singleton import Singleton

class RaiseIfError(Exception):
    def __init__(self, call):
        msg = fmt('raise if error with {call}')
        super(RaiseIfError, self).__init__(msg)

class AsyncRequests(Singleton):
    def __init__(self):
        self._loop = asyncio.get_event_loop()
        self.calls = []

    @property
    def call(self):
        if self.calls:
            return self.calls[-1]
        return None

    async def _request(self,
        method,
        url=None,
        auth=None,
        headers=None,
        json=None,
        raise_if=None,
        raise_ex=None,
        repeat_if=None,
        repeat_wait=3,
        repeat_delta=None):

        start = datetime.now()
        async with aiohttp.ClientSession(loop=self._loop) as session:
            repeat = 0
            while True:
                send_datetime = datetime.utcnow()
                async with session.request(
                    method,
                    url,
                    headers=headers,
                    auth=aiohttp.helpers.BasicAuth(*auth),
                    data=json_dumps(json) if json else None) as response:

                    text = await response.text()
                    recv_datetime = datetime.utcnow()
                    send = AttrDict(
                        method=method,
                        url=url,
                        json=json,
                        headers=headers,
                        datetime=send_datetime)
                    json = None
                    if response.headers['Content-Type'] == 'application/json':
                        json = await response.json()
                    recv = AttrDict(
                        headers=dict(response.headers.items()),
                        status=response.status,
                        text=windows2unix(text),
                        json=json,
                        repeat=repeat,
                        datetime=datetime.utcnow())
                    call = AttrDict(
                        response=response,
                        send=send,
                        recv=recv)
                self.calls += [call]
                if repeat_if and repeat_if(call):
                    delta = datetime.now() - start
                    if repeat_delta and delta < repeat_delta:
                        repeat += 1
                        print(fmt('{delta} < {repeat_delta}; repeat {repeat}'))
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
