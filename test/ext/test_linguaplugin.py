import os
from mako.ext.linguaplugin import LinguaMakoExtractor
from lingua.extractors import register_extractors
from .. import TemplateTest, template_base


class MockOptions:
    keywords = []
    domain = None


class ExtractMakoTestCase(TemplateTest):
    def test_extract(self):
        register_extractors()
        plugin = LinguaMakoExtractor({'comment-tags': 'TRANSLATOR'})
        messages = list(plugin(os.path.join(template_base, 'gettext.mako'), MockOptions()))
        msgids = [(m.msgid, m.msgid_plural) for m in messages]
        self.assertEqual(
                msgids,
                [
                    ('Page arg 1', None),
                    ('Page arg 2', None),
                    ('Begin', None),
                    ('Hi there!', None),
                    ('Hello', None),
                    ('Welcome', None),
                    ('Yo', None),
                    ('The', None),
                    ('bunny', 'bunnies'),
                    ('Goodbye', None),
                    ('Babel', None),
                    ('hella', 'hellas'),
                    ('The', None),
                    ('bunny', 'bunnies'),
                    ('Goodbye, really!', None),
                    ('P.S. byebye', None),
                    ('Top', None),
                    (u'foo', None),
                    ('hoho', None),
                    (u'bar', None),
                    ('Inside a p tag', None),
                    ('Later in a p tag', None),
                    ('No action at a distance.', None)])
