# Modified 2026-10-10: Dailymotion TLS compatibility and playback error handling.
"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import re
import six
from six.moves import urllib_request, urllib_parse, urllib_error
import gzip
import json
import ssl
from kodi_six import xbmc, xbmcvfs

TRANSLATEPATH = xbmcvfs.translatePath if six.PY3 else xbmc.translatePath
CERT_FILE = TRANSLATEPATH('special://xbmc/system/certs/cacert.pem')


def request(url, headers=None, post=None, cookie=None, timeout='20', return_url=False):
    _headers = {}
    if headers:
        _headers.update(headers)

    handlers = []
    ssl_context = ssl.create_default_context(cafile=CERT_FILE)
    # Align the embedded Python TLS defaults with current Python releases.
    # Certificate and hostname verification remain enabled.
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context.set_ciphers('ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:'
                           'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:'
                           'ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:'
                           'ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA384:'
                           'ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256:'
                           'DHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:'
                           'DHE-RSA-AES256-SHA256:DHE-RSA-AES128-SHA256')
    ssl_context.set_alpn_protocols(['http/1.1'])
    handlers += [urllib_request.HTTPSHandler(context=ssl_context)]
    opener = urllib_request.build_opener(*handlers)
    opener = urllib_request.install_opener(opener)

    if 'User-Agent' in _headers:
        pass
    else:
        _headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0'

    if 'Accept-Language' not in _headers:
        _headers['Accept-Language'] = 'en-US,en'

    if 'Accept-Encoding' in _headers:
        pass
    else:
        _headers['Accept-Encoding'] = 'gzip'

    if cookie is not None:
        if isinstance(cookie, dict):
            cookie = '; '.join(['{0}={1}'.format(x, y) for x, y in six.iteritems(cookie)])
        _headers['Cookie'] = cookie

    req = urllib_request.Request(url)

    if post is not None:
        post = json.dumps(post)
        post = six.ensure_binary(post)
        req = urllib_request.Request(url, post)
        req.add_header('Content-Type', 'application/json')

    _add_request_header(req, _headers)

    try:
        response = urllib_request.urlopen(req, timeout=int(timeout))
    except urllib_error.HTTPError as error:
        xbmc.log('DAILYMOTION - HTTP {0} from {1}'.format(error.code, urllib_parse.urlparse(url).hostname), xbmc.LOGERROR)
        return ''
    except urllib_error.URLError:
        xbmc.log('DAILYMOTION - Network error contacting {0}'.format(urllib_parse.urlparse(url).hostname), xbmc.LOGERROR)
        return ''

    result = response.read()
    encoding = None

    if response.headers.get('content-encoding', '').lower() == 'gzip':
        result = gzip.GzipFile(fileobj=six.BytesIO(result)).read()

    content_type = response.headers.get('content-type', '').lower()

    if 'charset=' in content_type:
        encoding = content_type.split('charset=')[-1]

    if encoding is None:
        epatterns = [r'<meta\s+http-equiv="Content-Type"\s+content="(?:.+?);\s+charset=(.+?)"',
                     r'xml\s*version.+encoding="([^"]+)']
        for epattern in epatterns:
            epattern = epattern.encode('utf8') if six.PY3 else epattern
            r = re.search(epattern, result, re.IGNORECASE)
            if r:
                encoding = r.group(1).decode('utf8') if six.PY3 else r.group(1)
                break

    if encoding is not None:
        result = result.decode(encoding, errors='ignore')
    else:
        xbmc.log('Unknown Page Encoding', xbmc.LOGDEBUG)
        result = result.decode('utf-8')  # fallback

    if 'json' in content_type:
        result = json.loads(result if isinstance(result, str) else result.decode('utf-8'))

    final_url = response.geturl()
    response.close()
    return (result, final_url) if return_url else result


def _add_request_header(_request, headers):
    try:
        if six.PY2:
            scheme = _request.get_type()
            host = _request.get_host()
        else:
            scheme = urllib_parse.urlparse(_request.get_full_url()).scheme
            host = _request.host

        referer = headers.get('Referer', '') or '%s://%s/' % (scheme, host)

        _request.add_unredirected_header('Host', host)
        _request.add_unredirected_header('Referer', referer)
        for key in headers:
            _request.add_header(key, headers[key])
    except BaseException:
        return
