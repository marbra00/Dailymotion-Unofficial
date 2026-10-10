# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the request path with real TLS contexts and offline HTTP responses."""
import ast
import gzip
import io
import json
import re
import ssl
import types
import unittest
from pathlib import Path
from unittest.mock import Mock
from urllib import error, parse, request


class ClientTLSTests(unittest.TestCase):
    def make_client(self, android, tickets=True):
        path = Path(__file__).resolve().parents[1] / 'plugin.video.dailymotion_unofficial/resources/lib/client.py'
        tree = ast.parse(path.read_text(encoding='utf-8'))
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
        context = ssl.create_default_context()
        if tickets:
            context.options &= ~ssl.OP_NO_TICKET
        else:
            context.options |= ssl.OP_NO_TICKET
        original_options = context.options
        factory = Mock(return_value=context)
        handlers = []

        def build_opener(*items):
            handlers.extend(items)
            return object()

        response = Mock()
        response.headers = {'content-type': 'application/x-mpegURL; charset=utf-8',
                            'content-encoding': 'gzip'}
        response.read.return_value = gzip.compress(b'#EXTM3U\n#EXTINF:6,\nsegment.ts\n')
        response.geturl.return_value = 'https://cdn.example/redirected.m3u8?signature=test'
        urllib = types.SimpleNamespace(Request=request.Request, HTTPSHandler=request.HTTPSHandler,
                                       build_opener=build_opener, install_opener=Mock(),
                                       urlopen=Mock(return_value=response))
        kodi = types.SimpleNamespace(getCondVisibility=Mock(return_value=android),
                                     LOGDEBUG=0, LOGERROR=3, log=Mock())
        tls = types.SimpleNamespace(create_default_context=factory, TLSVersion=ssl.TLSVersion,
                                    OP_NO_TICKET=ssl.OP_NO_TICKET)
        env = dict(ssl=tls, xbmc=kodi, CERT_FILE='fixture-cacert.pem', re=re, gzip=gzip,
                   json=json, urllib_request=urllib, urllib_parse=parse, urllib_error=error,
                   six=types.SimpleNamespace(PY2=False, PY3=True, BytesIO=io.BytesIO,
                                             iteritems=lambda value: value.items()))
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), 'exec'), env)
        return env, context, original_options, handlers, response, factory

    def test_android_disables_tickets_and_delivers_verified_context_to_http_handler(self):
        env, context, _, handlers, response, factory = self.make_client(android=True)
        body, final_url = env['request']('https://cdn.example/master.m3u8', return_url=True)
        self.assertTrue(body.startswith('#EXTM3U'))
        self.assertEqual(final_url, response.geturl.return_value)
        self.assertTrue(context.options & ssl.OP_NO_TICKET)
        self.assertIs(handlers[0]._context, context)
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertEqual(context.minimum_version, ssl.TLSVersion.TLSv1_2)
        factory.assert_called_once_with(cafile='fixture-cacert.pem')
        env['xbmc'].getCondVisibility.assert_called_once_with('System.Platform.Android')
        response.close.assert_called_once_with()

    def test_windows_preserves_existing_tls_options(self):
        for tickets in (True, False):
            with self.subTest(tickets=tickets):
                env, context, original, handlers, _, _ = self.make_client(android=False, tickets=tickets)
                self.assertTrue(env['request']('https://cdn.example/master.m3u8').startswith('#EXTM3U'))
                self.assertEqual(context.options, original)
                self.assertIs(handlers[0]._context, context)
                self.assertTrue(context.check_hostname)
                self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)

    def test_android_http_failure_still_returns_empty_result_without_logging_signed_url(self):
        env, _, _, _, _, _ = self.make_client(android=True)
        url = 'https://cdn.example/master.m3u8?signature=PRIVATE_TEST_TOKEN'
        env['urllib_request'].urlopen.side_effect = error.HTTPError(url, 403, 'Forbidden', {}, None)
        self.assertEqual(env['request'](url, return_url=True), '')
        text = env['xbmc'].log.call_args.args[0]
        self.assertIn('HTTP 403 from cdn.example', text)
        self.assertNotIn('PRIVATE_TEST_TOKEN', text)


if __name__ == '__main__':
    unittest.main()
