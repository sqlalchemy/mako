import unittest

from mako.lexer import Lexer
from mako import exceptions

class LexerTest(unittest.TestCase):
    def test_text_and_tag(self):
        template = """
<b>Hello world</b>
        <%def name="foo">
                this is a def.
        </%def>
        
        and some more text.
"""
        node = Lexer(template).parse()
        assert repr(node) == r"""TemplateNode({}, [Text('\n<b>Hello world</b>\n        ', (1, 1)), DefTag('def', {'name': 'foo'}, (3, 9), ["Text('\\n                this is a def.\\n        ', (3, 26))"]), Text('\n        \n        and some more text.\n', (5, 16))])"""

    def test_unclosed_tag(self):
        template = """
        
            <%def name="foo">
             other text
        """
        try:
            nodes = Lexer(template).parse()
            assert False
        except exceptions.SyntaxException, e:
            assert str(e) == "Unclosed tag: <%def> at line: 5 char: 9"

    def test_onlyclosed_tag(self):
        template = """
            <%def name="foo">
                foo
            </%def>
            
            </%namespace>
            
            hi.
        """
        try:
            nodes = Lexer(template).parse()
            assert False
        except exceptions.SyntaxException, e:
            assert str(e) == "Closing tag without opening tag: </%namespace> at line: 6 char: 13"

    def test_unmatched_tag(self):
        template = """
        <%namespace name="bar">
        <%def name="foo">
            foo
            </%namespace>
        </%def>
        
        
        hi.
"""
        try:
            nodes = Lexer(template).parse()
            assert False
        except exceptions.SyntaxException, e:
            assert str(e) == "Closing tag </%namespace> does not match tag: <%def> at line: 5 char: 13"

    def test_nonexistent_tag(self):
        template = """
            <%lala x="5"/>
        """
        try:
            node = Lexer(template).parse()
            assert False
        except exceptions.CompileException, e:
            assert str(e) == "No such tag: 'lala' at line: 2 char: 13"
    
    def test_text_tag(self):
        template = """
        # comment
        % if foo:
            hi
        % endif
        <%text>
            # more code
            
            % more code
            <%illegal compionent>/></>
            <%def name="laal">def</%def>
            
            
        </%text>

        <%def name="foo">this is foo</%def>
        
        % if bar:
            code
        % endif
        """
        node = Lexer(template).parse()
        print repr(node)
        assert repr(node) == """TemplateNode({}, [Comment('comment', (1, 1)), ControlLine('if', 'if foo:', False, (3, 1)), Text('            hi\n', (4, 1)), ControlLine('if', 'endif', True, (5, 1)), Text('        ', (6, 1)), TextTag('text', {}, (6, 9), []), Text('\n\n        ', (14, 17)), DefTag('def', {'name': 'foo'}, (16, 9), ["Text('this is foo', (16, 26))"]), Text('\n', (16, 44)), ControlLine('if', 'if bar:', False, (17, 1)), Text('            code\n', (19, 1)), ControlLine('if', 'endif', True, (20, 1)), Text('        ', (21, 1))])"""
        
    def test_def_syntax(self):
        template = """
        <%def lala>
            hi
        </%def>
"""
        try:
            node = Lexer(template).parse()
            assert False
        except exceptions.CompileException, e:
            assert str(e) == "Missing attribute(s): 'name' at line: 2 char: 9"
            
    def test_expr_in_attribute(self):
        """test some slightly trickier expressions.
        
        you can still trip up the expression parsing, though, unless we integrated really deeply somehow with AST."""
        template = """
            <%call expr="foo>bar and 'lala' or 'hoho'"/>
            <%call expr='foo<bar and hoho>lala and "x" + "y"'/>
        """
        nodes = Lexer(template).parse()
        #print nodes
        assert repr(nodes) == r"""TemplateNode({}, [Text('\n            ', (1, 1)), CallTag('call', {'expr': "foo>bar and 'lala' or 'hoho'"}, (2, 13), []), Text('\n            ', (2, 57)), CallTag('call', {'expr': 'foo<bar and hoho>lala and "x" + "y"'}, (3, 13), []), Text('\n        ', (3, 64))])"""
        
        
    def test_nesting(self):
        template = """
        
        <%namespace name="ns">
            <%def name="lala(hi, there)">
                <%call expr="something()"/>
            </%def>
        </%namespace>
        
        """
        nodes = Lexer(template).parse()
        assert repr(nodes) == r"""TemplateNode({}, [Text('\n        \n        ', (1, 1)), NamespaceTag('namespace', {'name': 'ns'}, (3, 9), ["Text('\\n            ', (3, 31))", 'DefTag(\'def\', {\'name\': \'lala(hi, there)\'}, (4, 13), ["Text(\'\\\\n                \', (4, 42))", "CallTag(\'call\', {\'expr\': \'something()\'}, (5, 17), [])", "Text(\'\\\\n            \', (5, 44))"])', "Text('\\n        ', (6, 20))"]), Text('\n        \n        ', (7, 22))])"""
    
    def test_code(self):
        template = """
        some text
        
        <%
            print "hi"
            for x in range(1,5):
                print x
        %>
        
        more text
        
        <%!
            import foo
        %>
        """
        nodes = Lexer(template).parse()
        #print nodes
        assert repr(nodes) == r"""TemplateNode({}, [Text('\n        some text\n        \n        ', (1, 1)), Code('\nprint "hi"\nfor x in range(1,5):\n    print x\n        \n', False, (4, 9)), Text('\n        \n        more text\n        \n        ', (8, 11)), Code('\nimport foo\n        \n', True, (12, 9)), Text('\n        ', (14, 11))])"""
    
    def test_code_and_tags(self):
        template = """
<%namespace name="foo">
    <%def name="x">
        this is x
    </%def>
    <%def name="y">
        this is y
    </%def>
</%namespace>

<%
    result = []
    data = get_data()
    for x in data:
        result.append(x+7)
%>

    result: <%call expr="foo.x(result)"/>
"""
        nodes = Lexer(template).parse()
        assert repr(nodes) == r"""TemplateNode({}, [Text('\n', (1, 1)), NamespaceTag('namespace', {'name': 'foo'}, (2, 1), ["Text('\\n    ', (2, 24))", 'DefTag(\'def\', {\'name\': \'x\'}, (3, 5), ["Text(\'\\\\n        this is x\\\\n    \', (3, 26))"])', "Text('\\n    ', (5, 18))", 'DefTag(\'def\', {\'name\': \'y\'}, (6, 5), ["Text(\'\\\\n        this is y\\\\n    \', (6, 26))"])', "Text('\\n', (8, 18))"]), Text('\n\n', (9, 14)), Code('\nresult = []\ndata = get_data()\nfor x in data:\n    result.append(x+7)\n\n', False, (11, 1)), Text('\n\n    result: ', (16, 3)), CallTag('call', {'expr': 'foo.x(result)'}, (18, 13), []), Text('\n', (18, 42))])"""


    def test_expression(self):
        template = """
        this is some ${text} and this is ${textwith | escapes, moreescapes}
        <%def name="hi">
            give me ${foo()} and ${bar()}
        </%def>
        ${hi()}
"""
        nodes = Lexer(template).parse()
        assert repr(nodes) == r"""TemplateNode({}, [Text('\n        this is some ', (1, 1)), Expression('text', [], (2, 22)), Text(' and this is ', (2, 29)), Expression('textwith ', ['escapes', 'moreescapes'], (2, 42)), Text('\n        ', (2, 76)), DefTag('def', {'name': 'hi'}, (3, 9), ["Text('\\n            give me ', (3, 25))", "Expression('foo()', [], (4, 21))", "Text(' and ', (4, 29))", "Expression('bar()', [], (4, 34))", "Text('\\n        ', (4, 42))"]), Text('\n        ', (5, 16)), Expression('hi()', [], (6, 9)), Text('\n', (6, 16))])"""

    def test_control_lines(self):
        template = """
text text la la
% if foo():
 mroe text la la blah blah
% endif

        and osme more stuff
        % for l in range(1,5):
    tex tesl asdl l is ${l} kfmas d
      % endfor
    tetx text
    
"""
        nodes = Lexer(template).parse()
        #print nodes
        assert repr(nodes) == r"""TemplateNode({}, [Text('\ntext text la la\n', (1, 1)), ControlLine('if', 'if foo():', False, (3, 1)), Text(' mroe text la la blah blah\n', (4, 1)), ControlLine('if', 'endif', True, (5, 1)), Text('\n        and osme more stuff\n', (6, 1)), ControlLine('for', 'for l in range(1,5):', False, (8, 1)), Text('    tex tesl asdl l is ', (9, 1)), Expression('l', [], (9, 24)), Text(' kfmas d\n', (9, 28)), ControlLine('for', 'endfor', True, (10, 1)), Text('    tetx text\n    \n', (11, 1))])"""
        
    def test_unmatched_control(self):
        template = """

        % if foo:
            % for x in range(1,5):
        % endif
"""
        try:
            nodes = Lexer(template).parse()
            assert False
        except exceptions.SyntaxException, e:
            assert str(e) == "Keyword 'endif' doesn't match keyword 'for' at line: 5 char: 1"

    def test_unmatched_control_2(self):
        template = """

        % if foo:
            % for x in range(1,5):
            % endlala
        % endif
"""
        try:
            nodes = Lexer(template).parse()
            assert False
        except exceptions.SyntaxException, e:
            assert str(e) == "Keyword 'endlala' doesn't match keyword 'for' at line: 5 char: 1"
    
    def test_ternary_control(self):
        template = """
        % if x:
            hi
        % elif y+7==10:
            there
        % elif lala:
            lala
        % else:
            hi
        % endif
"""    
        nodes = Lexer(template).parse()
        #print nodes
        assert repr(nodes) == r"""TemplateNode({}, [ControlLine('if', 'if x:', False, (1, 1)), Text('            hi\n', (3, 1)), ControlLine('elif', 'elif y+7==10:', False, (4, 1)), Text('            there\n', (5, 1)), ControlLine('elif', 'elif lala:', False, (6, 1)), Text('            lala\n', (7, 1)), ControlLine('else', 'else:', False, (8, 1)), Text('            hi\n', (9, 1)), ControlLine('if', 'endif', True, (10, 1))])"""
        
    def test_integration(self):
        template = """<%namespace name="foo" file="somefile.html"/>
 # inherit from foobar.html
<%inherit file="foobar.html"/>

<%def name="header">
     <div>header</div>
</%def>
<%def name="footer">
    <div> footer</div>
</%def>

<table>
    % for j in data():
    <tr>
        % for x in j:
            <td>Hello ${x| h}</td>
        % endfor
    </tr>
    % endfor
</table>
"""
        nodes = Lexer(template).parse()
        assert repr(nodes) == r"""TemplateNode({}, [NamespaceTag('namespace', {'name': 'foo', 'file': 'somefile.html'}, (1, 1), []), Text('\n', (1, 46)), Comment('inherit from foobar.html', (2, 1)), InheritTag('inherit', {'file': 'foobar.html'}, (3, 1), []), Text('\n\n', (3, 31)), DefTag('def', {'name': 'header'}, (5, 1), ["Text('\\n     <div>header</div>\\n', (5, 27))"]), Text('\n', (7, 14)), DefTag('def', {'name': 'footer'}, (8, 1), ["Text('\\n    <div> footer</div>\\n', (8, 27))"]), Text('\n\n<table>\n', (10, 14)), ControlLine('for', 'for j in data():', False, (13, 1)), Text('    <tr>\n', (14, 1)), ControlLine('for', 'for x in j:', False, (15, 1)), Text('            <td>Hello ', (16, 1)), Expression('x', ['h'], (16, 23)), Text('</td>\n', (16, 30)), ControlLine('for', 'endfor', True, (17, 1)), Text('    </tr>\n', (18, 1)), ControlLine('for', 'endfor', True, (19, 1)), Text('</table>\n', (20, 1))])"""

if __name__ == '__main__':
    unittest.main()
