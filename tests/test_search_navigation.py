# SPDX-License-Identifier: GPL-3.0-or-later
"""Search navigation tests with Kodi's folder-update guard simulated offline."""
import ast
import runpy
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from urllib import parse


ADDON = Path(__file__).resolve().parents[1] / 'plugin.video.dailymotion_unofficial'
SOURCE = ADDON / 'resources/lib/dailymotion.py'


class ListItem:
    def __init__(self, name):
        self.name = name
        self.properties = {}

    def setArt(self, art):
        pass

    def setProperty(self, name, value):
        self.properties[name] = value


class SearchNavigationTests(unittest.TestCase):
    def setUp(self):
        tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
        names = {'index', 'search', 'addDir', 'listVideos', 'listUsers', 'strip_tags',
                 'parameters_string_to_dict', 'addHistoryDir'}
        functions = [node for node in tree.body
                     if isinstance(node, ast.FunctionDef) and node.name in names]
        start = next(i for i, node in enumerate(tree.body)
                     if isinstance(node, ast.Assign)
                     and isinstance(node.targets[0], ast.Name)
                     and node.targets[0].id == 'params')
        self.dispatch = compile(ast.Module(body=tree.body[start:], type_ignores=[]),
                                str(SOURCE), 'exec')
        self.items = []
        self.ends = []
        self.updates = []
        self.requests = []
        self.guard = False
        self.blocked_updates = 0
        self.keyboard = Mock(return_value='nature')
        self.history = Mock()
        self.env = {
            'sys': types.SimpleNamespace(argv=['plugin://plugin.video.dailymotion_unofficial/',
                                                '7', '']),
            'pluginhandle': 7, 'addonID': 'plugin.video.dailymotion_unofficial',
            'urlMain': 'https://api.dailymotion.com', 'itemsPerPage': '50',
            'familyFilter': '0', 'language': 'de_DE', 'dmUser': '',
            'force_mode': False, '_ipath': 'images/', '_icon': 'icon.png',
            '_fanart': 'fanart.jpg', 'six': types.SimpleNamespace(PY2=False),
            'urllib_parse': parse, 're': __import__('re'),
            'datetime': __import__('datetime'), 'get_key': self.keyboard,
            'translation': lambda number: str(number), 'addtoHistory': self.history,
            'make_listitem': lambda name='', **kwargs: ListItem(name),
            'addFavDir': Mock(), 'getUrl2': self.get_response,
            'addLink': self.add_video,
            'xbmc': types.SimpleNamespace(executebuiltin=self.update_container),
            'xbmcplugin': types.SimpleNamespace(addDirectoryItem=self.add_item,
                                               addDirectoryItems=self.add_items,
                                               endOfDirectory=self.end_directory,
                                               setContent=Mock()),
        }
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(SOURCE), 'exec'),
             self.env)

    def add_item(self, handle, url, listitem, isFolder=False):
        self.items.append((url, listitem, isFolder))
        return True

    def add_items(self, handle, items, count):
        self.items.extend(items)
        return True

    def add_video(self, title, video, *args):
        self.items.append((video, ListItem(title), False))

    def end_directory(self, handle, **kwargs):
        self.ends.append((handle, len(self.items), kwargs))

    def get_response(self, url):
        self.requests.append(url)
        page = int(parse.parse_qs(parse.urlsplit(url).query)['page'][0])
        return {
            'list': [{'id': 'test-video', 'title': 'Test video', 'description': 'Test',
                      'duration': 60, 'owner.username': 'test-user', 'taken_time': 0,
                      'thumbnail_large_url': 'https://example.test/image.jpg',
                      'views_total': 1}],
            'has_more': page == 1, 'page': page,
        }

    def route(self, url, folder=True):
        if folder:
            self.items.clear()
        self.guard = folder
        self.env['pluginhandle'] = 7 if folder else -1
        self.env['sys'].argv = [url.split('?')[0], str(self.env['pluginhandle']),
                                '?' + url.split('?', 1)[1] if '?' in url else '']
        try:
            exec(self.dispatch, self.env)
        finally:
            self.guard = False

    def update_container(self, command):
        self.updates.append(command)
        if self.guard:
            self.blocked_updates += 1
            return
        self.route(command[len('Container.Update('):-1])

    def search_action(self):
        self.route('plugin://plugin.video.dailymotion_unofficial/')
        return next(item for item in self.items
                    if parse.parse_qs(parse.urlsplit(item[0]).query).get('mode') == ['search'])

    def test_search_is_an_action_and_other_directory_entries_remain_folders(self):
        url, item, folder = self.search_action()
        self.assertFalse(folder)
        self.assertEqual(item.properties['IsPlayable'], 'false')
        self.assertTrue(all(is_folder for path, _, is_folder in self.items if path != url))

    def test_search_opens_results_without_a_blocked_update_or_an_empty_completion(self):
        action = self.search_action()
        self.ends.clear()
        self.route(action[0], folder=action[2])
        self.assertEqual(self.blocked_updates, 0)
        self.assertEqual(len(self.updates), 1)
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(len(self.ends), 1)
        self.assertEqual(self.ends[0][1], 2)  # Video and next page, before completion.
        self.assertEqual(parse.parse_qs(parse.urlsplit(self.requests[0]).query)['search'],
                         ['nature'])

    def test_cancellation_empty_and_short_input_leave_the_current_page_untouched(self):
        action = self.search_action()
        current_page = list(self.items)
        for term in (None, '', 'a', 'ab'):
            with self.subTest(term=term):
                self.keyboard.return_value = term
                self.ends.clear()
                self.route(action[0], folder=action[2])
                self.assertEqual(self.ends, [])
                self.assertEqual(self.updates, [])
                self.assertEqual(self.requests, [])
                self.assertEqual(self.items, current_page)
                self.history.assert_not_called()

    def test_unicode_and_query_delimiters_round_trip_in_result_and_history_urls(self):
        action = self.search_action()
        term = 'München + Meer & Spaß'
        self.keyboard.return_value = term
        self.route(action[0], folder=action[2])
        query = parse.parse_qs(parse.urlsplit(self.requests[0]).query)
        self.assertEqual(query['search'], [term])
        self.assertEqual(query['localization'], ['de_DE'])
        self.assertEqual(query['limit'], ['50'])
        saved = self.history.call_args.args[0]
        self.assertEqual(saved['name'], term)
        self.assertEqual(parse.unquote_plus(saved['url']), self.requests[0])
        self.assertEqual(saved['mode'], 'listVideos')

    def test_next_page_and_return_to_results_do_not_reopen_the_keyboard(self):
        action = self.search_action()
        self.route(action[0], folder=action[2])
        result_url = self.updates[0][len('Container.Update('):-1]
        next_page = next(item[0] for item in self.items if item[2])
        self.route(next_page)
        self.assertEqual(parse.parse_qs(parse.urlsplit(self.requests[-1]).query)['page'],
                         ['2'])
        self.route(result_url)
        self.keyboard.assert_called_once()
        self.assertEqual(len(self.items), 2)

    def test_each_click_on_search_prompts_for_a_new_term(self):
        action = self.search_action()
        self.keyboard.side_effect = ['nature', 'ocean']
        self.route(action[0], folder=action[2])
        self.route(action[0], folder=action[2])
        self.assertEqual(self.keyboard.call_count, 2)
        self.assertEqual([parse.parse_qs(parse.urlsplit(url).query)['search'][0]
                          for url in self.requests], ['nature', 'ocean'])

    def test_saved_history_opens_results_without_a_search_dialog(self):
        action = self.search_action()
        self.route(action[0], folder=action[2])
        saved = self.history.call_args.args[0]
        self.items.clear()
        self.env['addHistoryDir']([saved])
        history_url = self.items[0][0]
        self.keyboard.reset_mock()
        self.route(history_url)
        self.keyboard.assert_not_called()
        self.assertEqual(len(self.items), 2)

    def test_users_without_a_username_are_skipped(self):
        self.env['getUrl2'] = lambda _: {'list': [
            {'username': ''},
            {'username': 'test-user', 'avatar_large_url': 'https://example.test/avatar.jpg',
             'videos_total': 3, 'views_total': 5},
            {'username': ''}], 'has_more': False}
        self.env['addUserDir'] = Mock()
        self.env['translation'] = lambda number: 'Aufrufe: {0}\nVideos: {1}'
        self.env['listUsers']('https://example.test/users?page=1')
        self.env['addUserDir'].assert_called_once()
        self.assertEqual(self.env['addUserDir'].call_args.args[0], 'test-user')
        self.assertEqual(self.env['addUserDir'].call_args.args[4], 'Aufrufe: 5\nVideos: 3')
        self.assertEqual(len(self.ends), 1)

    def test_entrypoint_does_not_append_a_second_main_menu_after_dispatch(self):
        self.route('plugin://plugin.video.dailymotion_unofficial/')
        initial_items = list(self.items)
        initial_ends = list(self.ends)
        self.run_entrypoint_after_dispatch()
        self.assertEqual(self.items, initial_items)
        self.assertEqual(self.ends, initial_ends)

    def test_entrypoint_does_not_render_a_directory_after_search_cancellation(self):
        action = self.search_action()
        self.keyboard.return_value = None
        self.ends.clear()
        self.route(action[0], folder=action[2])
        self.run_entrypoint_after_dispatch()
        self.assertEqual(self.ends, [])

    def run_entrypoint_after_dispatch(self):
        resources = types.ModuleType('resources')
        library = types.ModuleType('resources.lib')
        library.dailymotion = types.SimpleNamespace(index=self.env['index'])
        with patch.dict(sys.modules, {'resources': resources, 'resources.lib': library}):
            runpy.run_path(str(ADDON / 'default.py'))


if __name__ == '__main__':
    unittest.main()
