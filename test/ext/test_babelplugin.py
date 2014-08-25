import io
import mock
import unittest
from mako.ext.babelplugin import _split_comment
from mako.ext.babelplugin import extract
from mako.ext.babelplugin import extract_nodes


class Test_extract(unittest.TestCase):
    def test_parse_and_invoke_extract_nodes(self):
        input = io.BytesIO(b'<p>Hello world</p>')
        with mock.patch('mako.ext.babelplugin.extract_nodes') as extract_nodes:
            list(extract(input, [], [], {}))
            extract_nodes.assert_called_once_with([mock.ANY], [], [], {})
            self.assertEqual(
                    extract_nodes.mock_calls[0][1][0][0].content,
                    u'<p>Hello world</p>')

    def test_parse_python_expression(self):
        input = io.BytesIO(b'<p>${_("Message")}</p>')
        messages = list(extract(input, ['_'], [], {}))
        self.assertEqual(messages, [(1, '_', u'Message', [])])

    def test_python_gettext_call(self):
        input = io.BytesIO(b'<p>${_("Message")}</p>')
        messages = list(extract(input, ['_'], [], {}))
        self.assertEqual(messages, [(1, '_', u'Message', [])])

    def test_translator_comment(self):
        input = io.BytesIO(b'''
        <p>
          ## TRANSLATORS: This is a comment.
          ${_("Message")}
        </p>''')
        messages = list(extract(input, ['_'], ['TRANSLATORS:'], {}))
        self.assertEqual(
                messages,
                [(4, '_', u'Message', [u'TRANSLATORS: This is a comment.'])])


class Test_split_comment(unittest.TestCase):
    def test_empty_input(self):
        self.assertEqual(_split_comment(1, ''), [])

    def test_multiple_lines(self):
        self.assertEqual(
                _split_comment(5, 'one\ntwo\nthree'),
                [(5, 'one'), (6, 'two'), (7, 'three')])
