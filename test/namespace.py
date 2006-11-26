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

    def test_in_def(self):
        collection = lookup.TemplateLookup()
        collection.put_string("main.html", """
            <%namespace name="foo" file="ns.html"/>
            
            this is main.  ${bar()}
            <%def name="bar">
                this is bar, foo is ${foo.bar()}
            </%def>
        """)
        
        collection.put_string("ns.html", """
            <%def name="bar">
                this is ns.html->bar
            </%def>
        """)

        print collection.get_template("main.html").render()

    def test_in_remote_def(self):
        collection = lookup.TemplateLookup()
        collection.put_string("main.html", """
            <%namespace name="foo" file="ns.html"/>

            this is main.  ${bar()}
            <%def name="bar">
                this is bar, foo is ${foo.bar()}
            </%def>
        """)

        collection.put_string("ns.html", """
            <%def name="bar">
                this is ns.html->bar
            </%def>
        """)
        
        collection.put_string("index.html", """
            <%namespace name="main" file="main.html"/>
            
            this is index
            ${main.bar()}
        """)

        print collection.get_template("index.html").render()
    
    def test_inheritance(self):
        """test namespace initialization in a base inherited template that doesnt otherwise access the namespace"""
        collection = lookup.TemplateLookup()
        collection.put_string("base.html", """
            <%namespace name="foo" file="ns.html" inheritable="True"/>
            
            ${next.body()}
""")
        collection.put_string("ns.html", """
            <%def name="bar">
                this is ns.html->bar
            </%def>
        """)

        collection.put_string("index.html", """
            <%inherit file="base.html"/>
    
            this is index
            ${self.foo.bar()}
        """)
        
        print collection.get_template("index.html").render()
        
    def test_ccall(self):
        collection = lookup.TemplateLookup()
        collection.put_string("base.html", """
            <%namespace name="foo" file="ns.html" inheritable="True"/>

            ${next.body()}
    """)
        collection.put_string("ns.html", """
            <%def name="bar">
                this is ns.html->bar
                caller body: ${caller.body()}
            </%def>
        """)

        collection.put_string("index.html", """
            <%inherit file="base.html"/>

            this is index
            <%call expr="self.foo.bar()">
                call body
            </%call>
        """)

        print collection.get_template("index.html").render()

    def test_ccall_2(self):
        collection = lookup.TemplateLookup()
        collection.put_string("base.html", """
            <%namespace name="foo" file="ns1.html" inheritable="True"/>

            ${next.body()}
    """)
        collection.put_string("ns1.html", """
            <%namespace name="foo2" file="ns2.html"/>
            <%def name="bar">
                <%call expr="foo2.ns2_bar()">
                this is ns1.html->bar
                caller body: ${caller.body()}
                </%call>
            </%def>
        """)

        collection.put_string("ns2.html", """
            <%def name="ns2_bar">
                this is ns2.html->bar
                caller body: ${caller.body()}
            </%def>
        """)

        collection.put_string("index.html", """
            <%inherit file="base.html"/>

            this is index
            <%call expr="self.foo.bar()">
                call body
            </%call>
        """)

        print collection.get_template("index.html").render()
        
        
        
if __name__ == '__main__':
    unittest.main()
