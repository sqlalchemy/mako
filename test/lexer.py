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

    def test_expr_in_attribute(self):
        """test some slightly trickier expressions.
        
        you can still trip up the expression parsing, though, unless we integrated really deeply somehow with AST."""
        template = """
            <%call expr="foo>bar and 'lala' or 'hoho'"/>
            <%call expr='foo<bar and hoho>lala and "x" + "y"'/>
        """
        nodes = Lexer(template).parse()
        #print nodes
        assert repr(nodes) == r"""[Text('\n            ', (1, 1)), CallTag('call', {'expr': '"foo>bar and \'lala\' or \'hoho\'"'}, (2, 13), []), Text('\n            ', (2, 57)), CallTag('call', {'expr': '\'foo<bar and hoho>lala and "x" + "y"\''}, (3, 13), []), Text('\n        ', (3, 64))]"""
        
    def test_nesting(self):
        template = """
        
        <%namespace name="ns">
            <%component name="lala(hi, there)">
                <%call expr="something()"/>
            </%component>
        </%namespace>
        
        """
        nodes = Lexer(template).parse()
        assert repr(nodes) == r"""[Text('\n        \n        ', (1, 1)), NamespaceTag('namespace', {'name': '"ns"'}, (3, 9), ["Text('\\n            ', (3, 31))", 'ComponentTag(\'component\', {\'name\': \'"lala(hi, there)"\'}, (4, 13), ["Text(\'\\\\n                \', (4, 48))", \'CallTag(\\\'call\\\', {\\\'expr\\\': \\\'"something()"\\\'}, (5, 17), [])\', "Text(\'\\\\n            \', (5, 44))"])', "Text('\\n        ', (6, 26))"]), Text('\n        \n        ', (7, 22))]"""
        
if __name__ == '__main__':
    unittest.main()
