import unittest

try:
    import babel

    import os
    from mako.ext.babelplugin import extract

    class ExtractMakoTestCase(unittest.TestCase):
        def test_extract(self):
            mako_tmpl = open(os.path.join(os.path.dirname(__file__),
                                          'templates', 'gettext.mako'))
            messages = list(extract(mako_tmpl, {'_': None, 'gettext': None,
                                                'ungettext': (1, 2)},
                                    ['TRANSLATOR:'], {}))
            expected = \
                [(1, u'_', 'Page arg 1', []),
                 (1, u'_', 'Page arg 2', []),
                 (10, u'gettext', 'Begin', []),
                 (14, u'_', 'Hi there!', [u'Hi there!']),
                 (19, u'_', 'Hello', []),
                 (22, u'_', 'Welcome', []),
                 (25, u'_', 'Yo', []),
                 (36, u'_', 'The', [u'Ensure so and', u'so, thanks']),
                 (36, u'ungettext', ('bunny', 'bunnies', ''), []),
                 (41, u'_', 'Goodbye', [u'Good bye']),
                 (44, u'_', 'Babel', []),
                 (45, u'ungettext', ('hella', 'hellas'), []),
                 (62, u'_', 'Goodbye, really!', [u'HTML comment']),
                 (65, u'_', 'P.S. byebye', []),
                 (71, u'_', 'Top', [])]
            self.assertEqual(expected, messages)

except ImportError:
    import warnings
    warnings.warn('babel not installed: skipping babelplugin test',
                  RuntimeWarning, 1)

if __name__ == '__main__':
    unittest.main()
