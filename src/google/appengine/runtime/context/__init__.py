#!/usr/bin/env python
#
# Copyright 2007 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Wrapper for contextvars that can fall back to old os.environ hack."""
import os

import contextvars
from google.appengine.runtime.context import gae_headers
from google.appengine.runtime.context import oauth
from google.appengine.runtime.context import wsgi

READ_FROM_OS_ENVIRON = os.environ.get('READ_GAE_CONTEXT_FROM_OS_ENVIRON',
                                      'true') == 'true'


def get(key, default=None):
  """Read context from os.environ if READ_GAE_CONTEXT_FROM_OS_ENVIRON else, from contextvars."""
  if READ_FROM_OS_ENVIRON:
    return os.environ.get(key, default)
  ctxvar = vars(oauth).get(key, vars(gae_headers).get(key, vars(wsgi).get(key)))
  assert isinstance(ctxvar, contextvars.ContextVar)
  val = ctxvar.get(default)
  if isinstance(val, bool):
    return '1' if val else '0'
  return val


def put(key, value):
  """Write context to os.environ if READ_GAE_CONTEXT_FROM_OS_ENVIRON else, to contextvars."""
  if READ_FROM_OS_ENVIRON:
    os.environ[key] = value
    return
  ctxvar = vars(oauth).get(key, vars(gae_headers).get(key, vars(wsgi).get(key)))
  assert isinstance(ctxvar, contextvars.ContextVar)
  if isinstance(value, str):
    ctxvar.set(value == '1')
  ctxvar.set(value)


def clear():
  if READ_FROM_OS_ENVIRON:
    os.environ.clear()
    return
  for key in contextvars.copy_context():
    del key


def update(env):
  if READ_FROM_OS_ENVIRON:
    os.environ.update(env)
    return
  for key, value in env:
    put(key, value)


def pop(key):
  if READ_FROM_OS_ENVIRON:
    return os.environ.pop(key)
  del contextvars.copy_context().items()[key]


def items():
  if READ_FROM_OS_ENVIRON:
    return os.environ
  return {x.name: y for x, y in contextvars.copy_context().items()}


def init_from_wsgi_environ(wsgi_env):
  gae_headers.init_from_wsgi_environ(wsgi_env)
  wsgi.init_from_wsgi_environ(wsgi_env)
