from mako.template import Template
from mako import lookup
from util import flatten_result
import unittest

class NamespaceTest(unittest.TestCase):
    def test_inline(self):
        t = Template("""
        <%namespace name="x">
            <%def name="a">
                this is x a
            </%def>
            <%def name="b">
                this is x b, and heres ${a()}
            </%def>
        </%namespace>
        
        ${x.a()}
        
        ${x.b()}
""")
        assert flatten_result(t.render()) == "this is x a this is x b, and heres this is x a"

    def test_template(self):
        collection = lookup.TemplateLookup()

        collection.put_string('main.html', """
        <%namespace name="comp" file="defs.html"/>
        
        this is main.  ${comp.def1("hi")}
        ${comp.def2("there")}
""")

        collection.put_string('defs.html', """
        <%def name="def1(s)">
            def1: ${s}
        </%def>
        
        <%def name="def2(x)">
            def2: ${x}
        </%def>
""")

        assert flatten_result(collection.get_template('main.html').render()) == "this is main. def1: hi def2: there"
    
    def test_overload(self):
        collection = lookup.TemplateLookup()

        collection.put_string('main.html', """
        <%namespace name="comp" file="defs.html">
            <%def name="def1(x, y)">
                overridden def1 ${x}, ${y}
            </%def>
        </%namespace>

        this is main.  ${comp.def1("hi", "there")}
        ${comp.def2("there")}
    """)

        collection.put_string('defs.html', """
        <%def name="def1(s)">
            def1: ${s}
        </%def>

        <%def name="def2(x)">
            def2: ${x}
        </%def>
    """)

        assert flatten_result(collection.get_template('main.html').render()) == "this is main. overridden def1 hi, there def2: there"
        
if __name__ == '__main__':
    unittest.main()
