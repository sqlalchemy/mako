import unittest

from mako.codegen import Compiler
from mako.lexer import Lexer
from mako import exceptions

class CodeGenTest(unittest.TestCase):
    def test_gen_1(self):
        template = """
<html>
    <head>
        <title>${title}</title>
    </head>
    <body>
    <%
        x = get_data()
        log.debug("X is " + x)
    %>
    % for y in x:
        <p>${y}</p>
    % endfor

<%!
    from foo import get_data
%>
</html>        
    
"""
        node = Lexer(template).parse()
        code = Compiler(node).render()
        print code

    def test_gen_2(self):
        template = """
        <%component name="mycomp(x=5, y=7, *args, **kwargs)">
            hello world
        </%component>
 ${mycomp()}
"""
        node = Lexer(template).parse()
        code = Compiler(node).render()
        print code

if __name__ == '__main__':
    unittest.main()
