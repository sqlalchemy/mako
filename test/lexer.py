import unittest

from mako.lexer import Lexer
from mako import exceptions

class LexerTest(unittest.TestCase):
    def test_text_and_tag(self):
        template = """
<b>Hello world</b>
        <%component name="foo">
                this is a component.
        </%component>
        
        and some more text.
"""
        nodes = Lexer(template).parse()
        #print repr(nodes)
        assert repr(nodes) == r"""[Text('\n<b>Hello world</b>\n        ', (1, 1)), ComponentTag('component', {'name': '"foo"'}, (3, 9), ["Text('\\n                this is a component.\\n        ', (3, 32))"]), Text('\n        \n        and some more text.\n', (5, 22))]"""

    def test_unclosed_tag(self):
        template = """
        
            <%component name="foo">
             other text
        """
        try:
            nodes = Lexer(template).parse()
            assert False
        except exceptions.SyntaxException, e:
            assert str(e) == "Unclosed tag: <%component> at line: 5"
            
if __name__ == '__main__':
    unittest.main()
