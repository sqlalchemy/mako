import io
import mock
import unittest
from mako.ext.babelplugin import extract


class Test_extract(unittest.TestCase):
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
