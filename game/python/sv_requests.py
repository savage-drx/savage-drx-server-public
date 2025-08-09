import base64
import urllib.request
import urllib.parse
import core


class _Context:
    UTF_8 = 'utf-8'
    REQUEST_GET_TYPE = 'GET'
    REQUEST_POST_TYPE = 'POST'


def get_request(url, headers=None):
    auth_id = core.CvarGetString('sv_authid')
    token = core.CvarGetString('sv_authtoken')
    return _make_request(url, data=None, method=_Context.REQUEST_GET_TYPE,
                         username=auth_id, password=token, headers=headers)


def post_request(url, data=None, headers=None):
    if data is None:
        data = "{}"
    auth_id = core.CvarGetString('sv_authid')
    token = core.CvarGetString('sv_authtoken')
    return _make_request(url, data=data, method=_Context.REQUEST_POST_TYPE,
                         username=auth_id, password=token, headers=headers)


def _make_request(url, data=None, method=_Context.REQUEST_POST_TYPE, username=None, password=None, headers=None):
    if data is None:
        method = _Context.REQUEST_GET_TYPE

    request = urllib.request.Request(url, data=data.encode(_Context.UTF_8) if data else data, method=method)
    request.add_header('Content-Type', 'application/json')

    if headers is not None:
        for k, v in headers.items():
            request.add_header(k, v)

    if username is not None and password is not None:
        basic_auth = f"Basic {str(base64.b64encode(bytes(f'{username}:{password}', _Context.UTF_8)), _Context.UTF_8)}"
        request.add_header("Authorization", basic_auth)

    return urllib.request.urlopen(request)
