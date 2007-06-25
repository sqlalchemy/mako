import unittest

from mako.ext.turbogears import TGPlugin
from util import flatten_result, result_lines

tl = TGPlugin(options=dict(directories=['./test_htdocs']), extension='html')

class TestTGPlugun(unittest.TestCase):
    def test_basic(self):
        t = tl.load_template('/index.html')
        assert result_lines(t.render()) == [
            "this is index"
        ]
    def test_subdir(self):
        t = tl.load_template('/subdir/index.html')
        assert result_lines(t.render()) == [
            "this is sub index",
            "this is include 2"

        ]

        assert tl.load_template('/subdir/index.html').module_id == '_subdir_index_html'

    def test_basic_dot(self):
        t = tl.load_template('index')
        assert result_lines(t.render()) == [
            "this is index"
        ]
    def test_subdir_dot(self):
        t = tl.load_template('subdir.index')
        assert result_lines(t.render()) == [
            "this is sub index",
            "this is include 2"

        ]

        assert tl.load_template('subdir.index').module_id == '_subdir_index_html'
        