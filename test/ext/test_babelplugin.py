import io
import os
import unittest
from .. import TemplateTest, template_base, skip_if
from mako import compat

try:
    import babel.messages.extract as babel
except:
    babel = None

if babel is not None:
    from mako.ext.babelplugin import extract


def skip():
    return skip_if(
        lambda: not babel,
        'babel not installed: skipping babelplugin test')


class Test_extract(unittest.TestCase):
    @skip()
    def test_parse_python_expression(self):
        input = io.BytesIO(compat.b('<p>${_("Message")}</p>'))
        messages = list(extract(input, ['_'], [], {}))
        self.assertEqual(messages, [(1, '_', compat.u('Message'), [])])

    @skip()
    def test_python_gettext_call(self):
        input = io.BytesIO(compat.b('<p>${_("Message")}</p>'))
        messages = list(extract(input, ['_'], [], {}))
        self.assertEqual(messages, [(1, '_', compat.u('Message'), [])])

    @skip()
    def test_translator_comment(self):
        input = io.BytesIO(compat.b('''
        <p>
          ## TRANSLATORS: This is a comment.
          ${_("Message")}
        </p>'''))
        messages = list(extract(input, ['_'], ['TRANSLATORS:'], {}))
        self.assertEqual(
            messages,
            [(4, '_', compat.u('Message'),
                [compat.u('TRANSLATORS: This is a comment.')])])


class ExtractMakoTestCase(TemplateTest):
    @skip()
    def test_extract(self):
        mako_tmpl = open(os.path.join(template_base, 'gettext.mako'))
        messages = list(extract(mako_tmpl, {'_': None, 'gettext': None,
                                            'ungettext': (1, 2)},
                                ['TRANSLATOR:'], {}))
        expected = \
            [(1, '_', 'Page arg 1', []),
             (1, '_', 'Page arg 2', []),
             (10, 'gettext', 'Begin', []),
             (14, '_', 'Hi there!', ['TRANSLATOR: Hi there!']),
             (19, '_', 'Hello', []),
             (22, '_', 'Welcome', []),
             (25, '_', 'Yo', []),
             (36, '_', 'The', ['TRANSLATOR: Ensure so and', 'so, thanks']),
             (36, 'ungettext', ('bunny', 'bunnies', None), []),
             (41, '_', 'Goodbye', ['TRANSLATOR: Good bye']),
             (44, '_', 'Babel', []),
             (45, 'ungettext', ('hella', 'hellas', None), []),
             (62, '_', 'The', ['TRANSLATOR: Ensure so and', 'so, thanks']),
             (62, 'ungettext', ('bunny', 'bunnies', None), []),
             (68, '_', 'Goodbye, really!', ['TRANSLATOR: HTML comment']),
             (71, '_', 'P.S. byebye', []),
             (77, '_', 'Top', []),
             (83, '_', 'foo', []),
             (83, '_', 'hoho', []),
             (85, '_', 'bar', []),
             (92, '_', 'Inside a p tag', ['TRANSLATOR: <p> tag is ok?']),
             (95, '_', 'Later in a p tag', ['TRANSLATOR: also this']),
             (99, '_', 'No action at a distance.', []),
             ]
        self.assertEqual(expected, messages)
