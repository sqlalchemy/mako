from mako.template import Template
import unittest
from util import result_lines

class CacheTest(unittest.TestCase):
    def test_component(self):
        t = Template("""
        <%!
            callcount = [0]
        %>
        <%def name="foo" cached="True">
            this is foo
            <%
            callcount[0] += 1
            %>
        </%def>
    
        ${foo()}
        ${foo()}
        ${foo()}
        callcount: ${callcount}
""")
        print t.code
        print t.render()
        assert result_lines(t.render()) == [
            'this is foo',
            'this is foo',
            'this is foo',
            'callcount: [1]',
        ]

    def test_page(self):
        t = Template("""
        <%!
            callcount = [0]
        %>
        <%page cached="True"/>
        this is foo
        <%
        callcount[0] += 1
        %>
        callcount: ${callcount}
""")
        print t.code
        print t.render()
        print t.render()
        print t.render()
        

        
if __name__ == '__main__':
    unittest.main()