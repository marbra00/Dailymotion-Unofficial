# SPDX-License-Identifier: GPL-3.0-or-later
# Playback regression tests added 2026-10-10 with AI assistance.
"""Offline playback regression tests; run with python -m unittest discover -s tests."""
import ast
import re
import types
import unittest
from pathlib import Path
from urllib import parse


def load_resolver():
    path = Path(__file__).resolve().parents[1] / 'plugin.video.dailymotion_unofficial/resources/lib/dailymotion.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name in ('s', '_hls_variant', 'getStreamUrl')]
    env = {
        're': re, 'six': types.SimpleNamespace(string_types=(str,)), 'urllib_parse': parse,
        'language': 'en_GB', 'familyFilter': '1', 'maxVideoQuality': '480', '_UA': 'test-agent',
        '_icon': '', 'translation': lambda _: 'Playback unavailable',
        'xbmc': types.SimpleNamespace(LOGDEBUG=0, LOGERROR=3, log=lambda *args: None),
        'xbmcgui': types.SimpleNamespace(Dialog=lambda: types.SimpleNamespace(notification=lambda *args: None)),
    }
    # Import only resolver functions: normal addon import dispatches sys.argv and needs Kodi.
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), 'exec'), env)
    return env


class PlaylistTests(unittest.TestCase):
    def setUp(self):
        self.select = load_resolver()['_hls_variant']
        self.base = 'https://cdn.example/video/master.m3u8?signature=test'

    def test_http_failure_and_html_are_not_playlists(self):
        for body in ('', '<html>Forbidden</html>', '#EXTM3U\n'):
            self.assertIsNone(self.select(body, self.base, 480))

    def test_resolution_without_name_and_relative_uri(self):
        body = ('#EXTM3U\r\n#EXT-X-STREAM-INF:RESOLUTION=1280x720,BANDWIDTH=2000\r\n'
                '../720.m3u8\r\n#EXT-X-STREAM-INF:RESOLUTION=848x480,BANDWIDTH=1000\r\n'
                '# playlist comment\r\n480.m3u8?token=test#cell=abc\r\n')
        self.assertEqual(self.select(body, self.base, 480), 'https://cdn.example/video/480.m3u8?token=test')

    def test_quality_limit_and_uhd(self):
        body = ('#EXTM3U\n#EXT-X-STREAM-INF:NAME="1080@60",BANDWIDTH=5000\n1080.m3u8\n'
                '#EXT-X-STREAM-INF:NAME="480",BANDWIDTH=1000\n480.m3u8\n')
        self.assertTrue(self.select(body, self.base, 480).endswith('/480.m3u8'))
        self.assertTrue(self.select(body, self.base, 2160).endswith('/1080.m3u8'))

    def test_smallest_variant_when_limit_is_below_all_offered_variants(self):
        body = ('#EXTM3U\n#EXT-X-STREAM-INF:NAME="1080",BANDWIDTH=5000\n1080.m3u8\n'
                '#EXT-X-STREAM-INF:NAME="720",BANDWIDTH=2000\n720.m3u8\n')
        self.assertTrue(self.select(body, self.base, 240).endswith('/720.m3u8'))

    def test_direct_media_playlist_preserves_query(self):
        body = '#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nsegment.ts\n'
        self.assertEqual(self.select(body, self.base, 480), self.base)


class ResolverFailureTests(unittest.TestCase):
    def setUp(self):
        self.env = load_resolver()
        self.calls = []

    def test_403_empty_response_does_not_trigger_original_index_error(self):
        def request(url, **kwargs):
            self.calls.append(url)
            if '/metadata/' in url:
                return {'qualities': {'auto': [{'type': 'application/x-mpegURL',
                                               'url': 'https://cdn.example/master.m3u8'}]}}
            return ''  # client.request() returns this for HTTP 403
        self.env['client'] = types.SimpleNamespace(request=request)
        self.assertIsNone(self.env['getStreamUrl']('public-test-video'))
        self.assertEqual(len(self.calls), 4)  # two identities, fresh metadata per attempt

    def test_metadata_network_failure_is_bounded(self):
        def request(url, **kwargs):
            self.calls.append(url)
            return ''
        self.env['client'] = types.SimpleNamespace(request=request)
        self.assertIsNone(self.env['getStreamUrl']('public-test-video'))
        self.assertEqual(len(self.calls), 2)

    def test_live_media_playlist_and_subtitle_urls_are_preserved(self):
        def request(url, **kwargs):
            if '/metadata/' in url:
                return {'qualities': {'auto': [{'type': 'application/x-mpegURL',
                                               'url': 'https://cdn.example/live.m3u8?dvr=true&token=test'}]},
                        'subtitles': {'data': {'en': {'urls': ['https://cdn.example/subtitle.srt']}}}}
            self.assertNotIn('dvr=true&', url)
            return ('#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nsegment.ts', url)
        self.env['client'] = types.SimpleNamespace(request=request)
        stream, subs = self.env['getStreamUrl']('public-test-video', live=True)
        self.assertTrue(stream.startswith('https://cdn.example/live.m3u8?token=test|'))
        self.assertEqual(subs, ['https://cdn.example/subtitle.srt'])


if __name__ == '__main__':
    unittest.main()
