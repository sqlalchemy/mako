import unittest

try:
    import babel

    import os
    from mako.ext.babelplugin import extract

    class ExtractMakoTestCase(unittest.TestCase):
        def test_extract(self):
            mako_tmpl = open(os.path.join('test_htdocs', 'gettext.mako'))
            messages = list(extract(mako_tmpl, {'_': None, 'gettext': None,
                                                'ungettext': (1, 2)},
                                    ['TRANSLATOR:'], {}))
            expected = \
                [(1, '_', u'Page arg 1', []),
                 (1, '_', u'Page arg 2', []),
                 (10, 'gettext', u'Begin', []),
                 (14, '_', u'Hi there!', [u'TRANSLATOR: Hi there!']),
                 (19, '_', u'Hello', []),
                 (22, '_', u'Welcome', []),
                 (25, '_', u'Yo', []),
                 (36, '_', u'The', [u'TRANSLATOR: Ensure so and', u'so, thanks']),
                 (36, 'ungettext', (u'bunny', u'bunnies', None), []),
                 (41, '_', u'Goodbye', [u'TRANSLATOR: Good bye']),
                 (44, '_', u'Babel', []),
                 (45, 'ungettext', (u'hella', u'hellas', None), []),
                 (62, '_', u'Goodbye, really!', [u'TRANSLATOR: HTML comment']),
                 (65, '_', u'P.S. byebye', []),
                 (71, '_', u'Top', []), 
                 (77, '_', u'foo', []),
                 (77, '_', u'baz', []),
                 (79, '_', u'bar', [])
                 ]
            self.assertEqual(expected, messages)

except ImportError:
    import warnings
    warnings.warn('babel not installed: skipping babelplugin test',
                  RuntimeWarning, 1)

if __name__ == '__main__':
    unittest.main()
