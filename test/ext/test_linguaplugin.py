import io
import mock
import unittest
from mako.ext.linguaplugin import LinguaMakoExtractor


class MockOptions:
    keywords = []
    domain = None


class Test_LinguaMakoExtractor(unittest.TestCase):
    def test_parse_python_expression(self):
        plugin = LinguaMakoExtractor()
        plugin.options = MockOptions()
        plugin.filename = 'dummy.mako'
        input = io.BytesIO(b'<p>${_("Message")}</p>')
        messages = list(plugin.process_file(input))
        self.assertEqual(len(messages), 1)
