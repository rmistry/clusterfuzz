# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Gets a Google Issue Tracker HTTP client."""

from googleapiclient import discovery, errors
from google.auth import exceptions

import google.auth
import google_auth_httplib2
# import googleapiclient
import httplib2

# _DISCOVERY_URL = 'https://issuetracker.googleapis.com/$discovery/rest?version=v1'
_DISCOVERY_URL = ('https://issuetracker.googleapis.com/$discovery/rest?'
                  'version=v1&labels=GOOGLE_PUBLIC')
_SCOPE = 'https://www.googleapis.com/auth/buganizer'
_REQUEST_TIMEOUT = 60
HttpError = "test"

# Not finding this locally- not sure why..
HttpError = errors.HttpError

# TRY USING THIS TO CONNECT AFTER THE ATTEMPT
from clusterfuzz._internal.google_cloud_utils import credentials


def build_http(api='issuetracker', oauth_token=None, uberproxy_cookie=None):
    """Builds a httplib2.Http."""
    try:
      credentials, _ = google.auth.default()
      if credentials.requires_scopes:
        credentials = credentials.with_scopes([_SCOPE])
      return google_auth_httplib2.AuthorizedHttp(credentials)
    except google.auth.exceptions.DefaultCredentialsError as e:
      logging.error('Error when getting the application default credentials: %s',
                  str(e))
      return None


def build(api='issuetracker', http=None):
    """Builds a google api client for buganizer."""
    if not http:
        http = build_http(api)
    return discovery.build(
        api, 'v1', discoveryServiceUrl=_DISCOVERY_URL, http=http, cache_discovery=False
    )
