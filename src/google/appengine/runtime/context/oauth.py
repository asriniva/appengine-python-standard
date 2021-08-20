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
"""Declare oauth contextvars."""
import contextvars

OAUTH_AUTH_DOMAIN = contextvars.ContextVar('OAUTH_AUTH_DOMAIN')
OAUTH_EMAIL = contextvars.ContextVar('OAUTH_EMAIL')
OAUTH_USER_ID = contextvars.ContextVar('OAUTH_USER_ID')
OAUTH_CLIENT_ID = contextvars.ContextVar('OAUTH_CLIENT_ID')
OAUTH_IS_ADMIN = contextvars.ContextVar('OAUTH_IS_ADMIN')
OAUTH_ERROR_CODE = contextvars.ContextVar('OAUTH_ERROR_CODE')
OAUTH_ERROR_DETAIL = contextvars.ContextVar('OAUTH_ERROR_DETAIL')
OAUTH_LAST_SCOPE = contextvars.ContextVar('OAUTH_LAST_SCOPE')
