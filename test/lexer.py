import unittest

from mako.lexer import Lexer
from mako import exceptions
from util import flatten_result, result_lines
from mako.template import Template

class LexerTest(unittest.TestCase):
    def test_text_and_tag(self):
        template = """
<b>Hello world</b>
        <%def name="foo()">
                this is a def.
        </%def>
        
        and some more text.
"""
        node = Lexer(template).parse()
        assert repr(node) == r"""TemplateNode({}, [Text(u'\n<b>Hello world</b>\n        ', (1, 1)), DefTag(u'def', {u'name': u'foo()'}, (3, 9), ["Text(u'\\n                this is a def.\\n        ', (3, 28))"]), Text(u'\n        \n        and some more text.\n', (5, 16))])"""

    def test_unclosed_tag(self):
        template = """
        
            <%def name="foo()">
             other text
        """
        try:
            nodes = Lexer(template).parse()
            assert False
        except exceptions.SyntaxException, e:
            assert str(e) == "Unclosed tag: <%def> at line: 5 char: 9"

    def test_onlyclosed_tag(self):
        template = """
            <%def name="foo()">
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
        <%def name="foo()">
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
        ## comment
        % if foo:
            hi
        % endif
        <%text>
            # more code
            
            % more code
            <%illegal compionent>/></>
            <%def name="laal()">def</%def>
            
            
        </%text>

        <%def name="foo()">this is foo</%def>
        
        % if bar:
            code
        % endif
        """
        node = Lexer(template).parse()
        assert repr(node) == r"""TemplateNode({}, [Text(u'\n', (1, 1)), Comment(u'comment', (2, 1)), ControlLine(u'if', u'if foo:', False, (3, 1)), Text(u'            hi\n', (4, 1)), ControlLine(u'if', u'endif', True, (5, 1)), Text(u'        ', (6, 1)), TextTag(u'text', {}, (6, 9), ['Text(u\'\\n            # more code\\n            \\n            % more code\\n            <%illegal compionent>/></>\\n            <%def name="laal()">def</%def>\\n            \\n            \\n        \', (6, 16))']), Text(u'\n\n        ', (14, 17)), DefTag(u'def', {u'name': u'foo()'}, (16, 9), ["Text(u'this is foo', (16, 28))"]), Text(u'\n        \n', (16, 46)), ControlLine(u'if', u'if bar:', False, (18, 1)), Text(u'            code\n', (19, 1)), ControlLine(u'if', u'endif', True, (20, 1)), Text(u'        ', (21, 1))])"""
        
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
    
    def test_def_syntax_2(self):
        template = """
        <%def name="lala">
            hi
        </%def>
    """
        try:
            node = Lexer(template).parse()
            assert False
        except exceptions.CompileException, e:
            assert str(e) == "Missing parenthesis in %def at line: 2 char: 9"
                
    def test_expr_in_attribute(self):
        """test some slightly trickier expressions.
        
        you can still trip up the expression parsing, though, unless we integrated really deeply somehow with AST."""
        template = """
            <%call expr="foo>bar and 'lala' or 'hoho'"/>
            <%call expr='foo<bar and hoho>lala and "x" + "y"'/>
        """
        nodes = Lexer(template).parse()
        #print nodes
        assert repr(nodes) == r"""TemplateNode({}, [Text(u'\n            ', (1, 1)), CallTag(u'call', {u'expr': u"foo>bar and 'lala' or 'hoho'"}, (2, 13), []), Text(u'\n            ', (2, 57)), CallTag(u'call', {u'expr': u'foo<bar and hoho>lala and "x" + "y"'}, (3, 13), []), Text(u'\n        ', (3, 64))])"""
        
    def test_pagetag(self):
        template = """
            <%page cached="True", args="a, b"/>
            
            some template
        """    
        nodes = Lexer(template).parse()
        assert repr(nodes) == r"""TemplateNode({}, [Text(u'\n            ', (1, 1)), PageTag(u'page', {u'cached': u'True', u'args': u'a, b'}, (2, 13), []), Text(u'\n            \n            some template\n        ', (2, 48))])"""
        
    def test_nesting(self):
        template = """
        
        <%namespace name="ns">
            <%def name="lala(hi, there)">
                <%call expr="something()"/>
            </%def>
        </%namespace>
        
        """
        nodes = Lexer(template).parse()
        assert repr(nodes) == r"""TemplateNode({}, [Text(u'\n        \n        ', (1, 1)), NamespaceTag(u'namespace', {u'name': u'ns'}, (3, 9), ["Text(u'\\n            ', (3, 31))", 'DefTag(u\'def\', {u\'name\': u\'lala(hi, there)\'}, (4, 13), ["Text(u\'\\\\n                \', (4, 42))", "CallTag(u\'call\', {u\'expr\': u\'something()\'}, (5, 17), [])", "Text(u\'\\\\n            \', (5, 44))"])', "Text(u'\\n        ', (6, 20))"]), Text(u'\n        \n        ', (7, 22))])"""
    
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
        assert repr(nodes) == r"""TemplateNode({}, [Text(u'\n        some text\n        \n        ', (1, 1)), Code(u'\nprint "hi"\nfor x in range(1,5):\n    print x\n        \n', False, (4, 9)), Text(u'\n        \n        more text\n        \n        ', (8, 11)), Code(u'\nimport foo\n        \n', True, (12, 9)), Text(u'\n        ', (14, 11))])"""
    
    def test_code_and_tags(self):
        template = """
<%namespace name="foo">
    <%def name="x()">
        this is x
    </%def>
    <%def name="y()">
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
        assert repr(nodes) == r"""TemplateNode({}, [Text(u'\n', (1, 1)), NamespaceTag(u'namespace', {u'name': u'foo'}, (2, 1), ["Text(u'\\n    ', (2, 24))", 'DefTag(u\'def\', {u\'name\': u\'x()\'}, (3, 5), ["Text(u\'\\\\n        this is x\\\\n    \', (3, 22))"])', "Text(u'\\n    ', (5, 12))", 'DefTag(u\'def\', {u\'name\': u\'y()\'}, (6, 5), ["Text(u\'\\\\n        this is y\\\\n    \', (6, 22))"])', "Text(u'\\n', (8, 12))"]), Text(u'\n\n', (9, 14)), Code(u'\nresult = []\ndata = get_data()\nfor x in data:\n    result.append(x+7)\n\n', False, (11, 1)), Text(u'\n\n    result: ', (16, 3)), CallTag(u'call', {u'expr': u'foo.x(result)'}, (18, 13), []), Text(u'\n', (18, 42))])"""

    def test_expression(self):
        template = """
        this is some ${text} and this is ${textwith | escapes, moreescapes}
        <%def name="hi()">
            give me ${foo()} and ${bar()}
        </%def>
        ${hi()}
"""
        nodes = Lexer(template).parse()
        assert repr(nodes) == r"""TemplateNode({}, [Text(u'\n        this is some ', (1, 1)), Expression(u'text', [], (2, 22)), Text(u' and this is ', (2, 29)), Expression(u'textwith ', ['escapes', 'moreescapes'], (2, 42)), Text(u'\n        ', (2, 76)), DefTag(u'def', {u'name': u'hi()'}, (3, 9), ["Text(u'\\n            give me ', (3, 27))", "Expression(u'foo()', [], (4, 21))", "Text(u' and ', (4, 29))", "Expression(u'bar()', [], (4, 34))", "Text(u'\\n        ', (4, 42))"]), Text(u'\n        ', (5, 16)), Expression(u'hi()', [], (6, 9)), Text(u'\n', (6, 16))])"""
        

    def test_tricky_expression(self):
        template = """
        
            ${x and "|" or "hi"}
        """
        nodes = Lexer(template).parse()
        assert repr(nodes) == r"""TemplateNode({}, [Text(u'\n        \n            ', (1, 1)), Expression(u'x and "|" or "hi"', [], (3, 13)), Text(u'\n        ', (3, 33))])"""

        template = """
        
            ${hello + '''heres '{|}' text | | }''' | escape1}
        """
        nodes = Lexer(template).parse()
        assert repr(nodes) == r"""TemplateNode({}, [Text(u'\n        \n            ', (1, 1)), Expression(u"hello + '''heres '{|}' text | | }''' ", ['escape1'], (3, 13)), Text(u'\n        ', (3, 62))])"""

    def test_tricky_code(self):
        template = """<% print 'hi %>' %>"""
        nodes = Lexer(template).parse()
        assert repr(nodes) == r"""TemplateNode({}, [Code(u"print 'hi %>' \n", False, (1, 1))])"""
        
        template = r"""
        <%
            lines = src.split('\n')
        %>
"""
        nodes = Lexer(template).parse()
        
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
        assert repr(nodes) == r"""TemplateNode({}, [Text(u'\ntext text la la\n', (1, 1)), ControlLine(u'if', u'if foo():', False, (3, 1)), Text(u' mroe text la la blah blah\n', (4, 1)), ControlLine(u'if', u'endif', True, (5, 1)), Text(u'\n        and osme more stuff\n', (6, 1)), ControlLine(u'for', u'for l in range(1,5):', False, (8, 1)), Text(u'    tex tesl asdl l is ', (9, 1)), Expression(u'l', [], (9, 24)), Text(u' kfmas d\n', (9, 28)), ControlLine(u'for', u'endfor', True, (10, 1)), Text(u'    tetx text\n    \n', (11, 1))])"""

    def test_control_lines_2(self):
        template = \
"""


% for file in requestattr['toc'].filenames:
    x
% endfor
"""
        nodes = Lexer(template).parse()
        assert repr(nodes) == r"""TemplateNode({}, [Text(u'\n\n\n', (1, 1)), ControlLine(u'for', u"for file in requestattr['toc'].filenames:", False, (4, 1)), Text(u'    x\n', (5, 1)), ControlLine(u'for', u'endfor', True, (6, 1))])"""

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
        assert repr(nodes) == r"""TemplateNode({}, [Text(u'\n', (1, 1)), ControlLine(u'if', u'if x:', False, (2, 1)), Text(u'            hi\n', (3, 1)), ControlLine(u'elif', u'elif y+7==10:', False, (4, 1)), Text(u'            there\n', (5, 1)), ControlLine(u'elif', u'elif lala:', False, (6, 1)), Text(u'            lala\n', (7, 1)), ControlLine(u'else', u'else:', False, (8, 1)), Text(u'            hi\n', (9, 1)), ControlLine(u'if', u'endif', True, (10, 1))])"""
        
    def test_integration(self):
        template = """<%namespace name="foo" file="somefile.html"/>
 ## inherit from foobar.html
<%inherit file="foobar.html"/>

<%def name="header()">
     <div>header</div>
</%def>
<%def name="footer()">
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
        print repr(nodes)
        assert repr(nodes) == r"""TemplateNode({}, [NamespaceTag(u'namespace', {u'name': u'foo', u'file': u'somefile.html'}, (1, 1), []), Text(u'\n', (1, 46)), Comment(u'inherit from foobar.html', (2, 1)), InheritTag(u'inherit', {u'file': u'foobar.html'}, (3, 1), []), Text(u'\n\n', (3, 31)), DefTag(u'def', {u'name': u'header()'}, (5, 1), ["Text(u'\\n     <div>header</div>\\n', (5, 23))"]), Text(u'\n', (7, 8)), DefTag(u'def', {u'name': u'footer()'}, (8, 1), ["Text(u'\\n    <div> footer</div>\\n', (8, 23))"]), Text(u'\n\n<table>\n', (10, 8)), ControlLine(u'for', u'for j in data():', False, (13, 1)), Text(u'    <tr>\n', (14, 1)), ControlLine(u'for', u'for x in j:', False, (15, 1)), Text(u'            <td>Hello ', (16, 1)), Expression(u'x', ['h'], (16, 23)), Text(u'</td>\n', (16, 30)), ControlLine(u'for', u'endfor', True, (17, 1)), Text(u'    </tr>\n', (18, 1)), ControlLine(u'for', u'endfor', True, (19, 1)), Text(u'</table>\n', (20, 1))])"""

    def test_crlf(self):
        template = file("./test_htdocs/crlf.html").read()
        nodes = Lexer(template).parse()
        assert repr(nodes) == r"""TemplateNode({}, [Text(u'<html>\r\n\r\n', (1, 1)), PageTag(u'page', {}, (3, 1), []), Text(u'\r\n\r\nlike the name says.\r\n\r\n', (3, 9)), ControlLine(u'for', u'for x in [1,2,3]:', False, (7, 1)), Text(u'        ', (8, 1)), Expression(u'x', [], (8, 9)), Text(u'', (8, 13)), ControlLine(u'for', u'endfor', True, (9, 1)), Text(u'\r\n', (10, 1)), DefTag(u'def', {u'name': u'hi()'}, (11, 1), ["Text(u'\\r\\n    hi!\\r\\n', (11, 19))"]), Text(u'\r\n\r\n</html>', (13, 8))])"""
        assert flatten_result(Template(template).render()) == """<html> like the name says. 1 2 3 </html>"""
    
    def test_comments(self):
        template = """
<style>
 #someselector
 # other non comment stuff
</style>
## a comment

# also not a comment

   ## this is a comment
   
this is ## not a comment

#* multiline
comment
*#

hi
"""
        nodes = Lexer(template).parse()
        assert repr(nodes) == r"""TemplateNode({}, [Text(u'\n<style>\n #someselector\n # other non comment stuff\n</style>\n', (1, 1)), Comment(u'a comment', (6, 1)), Text(u'\n# also not a comment\n\n', (7, 1)), Comment(u'this is a comment', (10, 1)), Text(u'   \nthis is ## not a comment\n\n', (11, 1)), Comment(u' multiline\ncomment\n', (14, 1)), Text(u'\n\nhi\n', (16, 3))])"""
        
if __name__ == '__main__':
    unittest.main()
