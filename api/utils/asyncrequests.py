#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import aiohttp
import asyncio

from json import dumps as json_dumps
from pprint import pprint, pformat
from attrdict import AttrDict
from datetime import datetime
from urllib.parse import urlparse
from fnmatch import fnmatch

from utils.format import fmt, pfmt
from utils.newline import windows2unix
from utils.dictionary import merge
from utils.singleton import Singleton
from utils.exceptions import AutocertError

class RaiseIfError(AutocertError):
    def __init__(self, call):
        message = fmt('raise if error with {call}')
        super(RaiseIfError, self).__init__(message)

class ConflictingProxyEnv(Exception):
    def __init__(self, key, values):
        message = fmt('too many proxy values={values} for key={key} in env')
        super(ConflictingProxyEnv, self).__init__(message)

def get_proxy_value_from_env(key):
    values = [
        os.environ.get(key.lower(), None),
        os.environ.get(key.upper(), None),
    ]
    values = list(set([value for value in values if value is not None]))
    if len(values) == 2:
        raise ConflictingProxyEnv(key, values)
    return values[0] if values else None

def ensure_http(url):
    if url:
        p = urlparse(url)
        if p.scheme in ('', 'https'):
            return 'http://'+url
    return url

class AsyncRequests(Singleton):
    def __init__(self):
        self.calls = []
        self._loop = asyncio.get_event_loop()
        self.http_proxy = ensure_http(get_proxy_value_from_env('http_proxy'))
        self.https_proxy = ensure_http(get_proxy_value_from_env('https_proxy'))
        self.no_proxy = get_proxy_value_from_env('no_proxy')
        self.no_proxies = re.split('[, ]+', self.no_proxy) if self.no_proxy else []

    @property
    def call(self):
        if self.calls:
            return self.calls[-1]
        return None

    def proxy(self, url):
        p = urlparse(url)
        if any([fnmatch(p.hostname, no_proxy) for no_proxy in self.no_proxies]):
            return None
        return {
            'http': self.http_proxy,
            'https': self.https_proxy,
        }[p.scheme]

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
        repeat_delta=None,
        verify_ssl=True,
        **kwargs):

        start = datetime.now()
        connector = aiohttp.TCPConnector(verify_ssl=verify_ssl)
        async with aiohttp.ClientSession(connector=connector, loop=self._loop) as session:
            repeat = 0
            while True:
                send_datetime = datetime.utcnow()
                proxy = self.proxy(url)
                async with session.request(
                    method,
                    url,
                    headers=headers,
                    proxy=proxy,
                    auth=aiohttp.helpers.BasicAuth(*auth),
                    data=json_dumps(json) if json else None,
                    **kwargs) as response:

                    text = await response.text()
                    recv_datetime = datetime.utcnow()
                    send = AttrDict(
                        method=method,
                        url=url,
                        json=json,
                        proxy=proxy,
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
                        pfmt('{delta} < {repeat_delta}; repeat {repeat}')
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
