# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Chromium issue tracker manager functions."""

from http import client as http_client
import json
import logging

from googleapiclient import discovery, errors
from google.auth import exceptions

import google.auth
import google_auth_httplib2


_DISCOVERY_URI = ('https://issuetracker.googleapis.com/$discovery/rest?version=v1&labels=GOOGLE_PUBLIC')

EMAIL_SCOPE = 'https://www.googleapis.com/auth/userinfo.email'

BUGANIZER_SCOPES = 'https://www.googleapis.com/auth/buganizer'
MAX_DISCOVERY_RETRIES = 3
MAX_REQUEST_RETRIES = 5

_NUM_RETRIES = 3


class IssueTrackerError(Exception):
  """Base issue tracker error."""


class IssueTrackerNotFoundError(IssueTrackerError):
  """Not found error."""


class IssueTrackerPermissionError(IssueTrackerError):
  """Permission error."""


def ServiceAccountHttp(scope=EMAIL_SCOPE, timeout=None):
  """Returns the Credentials of the service account if available."""
  assert scope, "ServiceAccountHttp scope must not be None."
  credentials = _GetAppDefaultCredentials(scope)
  http = google_auth_httplib2.AuthorizedHttp(credentials)
  if timeout:
    http.timeout = timeout
  return http


def _GetAppDefaultCredentials(scope=None):
  try:
    credentials, _ = google.auth.default()
    if scope and credentials.requires_scopes:
      credentials = credentials.with_scopes([scope])
    return credentials
  except google.auth.exceptions.DefaultCredentialsError as e:
    logging.error('Error when getting the application default credentials: %s',
                  str(e))
    return None


class ChromiumIssueTrackerManager:
  """ Chromium issue tracker manager. """

  def __init__(self):
    """ Initializes an object to communicate to Buganizer. """
    http = ServiceAccountHttp(BUGANIZER_SCOPES)
    http.timeout = 30
    # Retry connecting at least 3 times.
    attempt = 1
    while attempt != MAX_DISCOVERY_RETRIES:
      try:
        self._service = discovery.build(
            'issuetracker', 'v1', discoveryServiceUrl=_DISCOVERY_URI, http=http)
        break
      except http_client.HTTPException as e:
        logging.error('Attempt #%d: %s', attempt, e)
        if attempt == MAX_DISCOVERY_RETRIES:
          raise
      attempt += 1

  @property
  def client(self):
    """HTTP Client."""
    return self._service.build()

  def _execute(self, request):
    """Executes a request."""
    http = None
    for _ in range(2):
      try:
        return request.execute(num_retries=_NUM_RETRIES, http=http)
      except exceptions.RefreshError:
        # Rebuild client and retry request.
        http = self._service.build_http()
        self._client = self._service.build(http=http)
      except errors.HttpError as e:
        if e.resp.status == 404:
          raise IssueTrackerNotFoundError(str(e))
        if e.resp.status == 403:
          raise IssueTrackerPermissionError(str(e))
        raise IssueTrackerError(str(e))

  def test_edit(self, issue_id):
    """Edit an issue"""
    update_body = {
        "add": {},
        "addMask": "",
        "remove": {},
        "removeMask": "",
    }
    update_body["issueComment"] = {
        "comment": "test comment",
    }
    request = self._service.issues().modify(
        issueId=issue_id, body=update_body)
    return self._execute(request)


if __name__ == '__main__':
  c = ChromiumIssueTrackerManager()
  print(dir(c._service))
  result = c.test_edit('302703317')
  print(result)
  print(dir(result))

