from mako.template import Template
import unittest
from util import result_lines

class CallTest(unittest.TestCase):
    def test_call(self):
        t = Template("""
        <%def name="foo()">
            hi im foo ${caller.body(y=5)}
        </%def>
        
        <%call expr="foo()" args="y, **kwargs">
            this is the body, y is ${y}
        </%call>
""")
        assert result_lines(t.render()) == ['hi im foo', 'this is the body, y is 5']


    def test_compound_call(self):
        t = Template("""

        <%def name="bar()">
            this is bar
        </%def>
        
        <%def name="comp1()">
            this comp1 should not be called
        </%def>
        
        <%def name="foo()">
            foo calling comp1: ${caller.comp1(x=5)}
            foo calling body: ${caller.body()}
        </%def>
        
        <%call expr="foo()">
            <%def name="comp1(x)">
                this is comp1, ${x}
            </%def>
            this is the body, ${comp1(6)}
        </%call>
        ${bar()}

""")

        assert result_lines(t.render()) == ['foo calling comp1:', 'this is comp1, 5', 'foo calling body:', 'this is the body,', 'this is comp1, 6', 'this is bar']

    def test_chained_call(self):
        """test %calls that are chained through their targets"""
        t = Template("""
            <%def name="a()">
                this is a. 
                <%call expr="b()">
                    this is a's ccall.  heres my body: ${caller.body()}
                </%call>
            </%def>
            <%def name="b()">
                this is b.  heres  my body: ${caller.body()}
                whats in the body's caller's body ?
                ${context.caller_stack[-2].body()}
            </%def>
            
            <%call expr="a()">
                heres the main templ call
            </%call>
            
""")
        assert result_lines(t.render()) == [
            'this is a.',
            'this is b. heres my body:',
            "this is a's ccall. heres my body:",
            'heres the main templ call',
            "whats in the body's caller's body ?",
            'heres the main templ call'
        ]

    def test_nested_call(self):
        """test %calls that are nested inside each other"""
        t = Template("""
            <%def name="foo()">
                ${caller.body(x=10)}
            </%def>

            x is ${x}
            <%def name="bar()">
                bar: ${caller.body()}
            </%def>

            <%call expr="foo()" args="x">
                this is foo body: ${x}

                <%call expr="bar()">
                    this is bar body: ${x}
                </%call>
            </%call>
""")
        assert result_lines(t.render(x=5)) == [
            "x is 5",
            "this is foo body: 10",
            "bar:",
            "this is bar body: 10"
        ]
        
    def test_nested_call_2(self):
        t = Template("""
            x is ${x}
            <%def name="foo()">
                ${caller.foosub(x=10)}
            </%def>

            <%def name="bar()">
                bar: ${caller.barsub()}
            </%def>

            <%call expr="foo()">
                <%def name="foosub(x)">
                this is foo body: ${x}
                
                <%call expr="bar()">
                    <%def name="barsub()">
                    this is bar body: ${x}
                    </%def>
                </%call>
                
                </%def>

            </%call>
""")
        assert result_lines(t.render(x=5)) == [
            "x is 5",
            "this is foo body: 10",
            "bar:",
            "this is bar body: 10"
        ]
        
    def test_chained_call_in_nested(self):
        t = Template("""
            <%def name="embedded()">
            <%def name="a()">
                this is a. 
                <%call expr="b()">
                    this is a's ccall.  heres my body: ${caller.body()}
                </%call>
            </%def>
            <%def name="b()">
                this is b.  heres  my body: ${caller.body()}
                whats in the body's caller's body ? ${context.caller_stack[-2].body()}
            </%def>

            <%call expr="a()">
                heres the main templ call
            </%call>
            </%def>
            ${embedded()}
""")
        assert result_lines(t.render()) == [
            'this is a.',
            'this is b. heres my body:',
            "this is a's ccall. heres my body:",
            'heres the main templ call',
            "whats in the body's caller's body ?",
            'heres the main templ call'
        ]
        
    def test_call_in_nested(self):
        t = Template("""
            <%def name="a()">
                this is a ${b()}
                <%def name="b()">
                    this is b
                    <%call expr="c()">
                        this is the body in b's call
                    </%call>
                </%def>
                <%def name="c()">
                    this is c: ${caller.body()}
                </%def>
            </%def>
        ${a()}
""")
        assert result_lines(t.render()) == ['this is a', 'this is b', 'this is c:', "this is the body in b's call"]

        
    def test_call_in_nested_2(self):
        t = Template("""
            <%def name="a()">
                <%def name="d()">
                    not this d
                </%def>
                this is a ${b()}
                <%def name="b()">
                    <%def name="d()">
                        not this d either
                    </%def>
                    this is b
                    <%call expr="c()">
                        <%def name="d()">
                            this is d
                        </%def>
                        this is the body in b's call
                    </%call>
                </%def>
                <%def name="c()">
                    this is c: ${caller.body()}
                    the embedded "d" is: ${caller.d()}
                </%def>
            </%def>
        ${a()}
""")
        assert result_lines(t.render()) == ['this is a', 'this is b', 'this is c:', "this is the body in b's call", 'the embedded "d" is:', 'this is d']

class SelfCacheTest(unittest.TestCase):
    def test_basic(self):
        t = Template("""
        <%!
            cached = None
        %>
        <%def name="foo()">
            <% 
                global cached
                if cached:
                    return "cached: " + cached
                context.push_buffer()
            %>
            this is foo
            <%
                buf = context.pop_buffer()
                cached = buf.getvalue()
                return cached
            %>
        </%def>
        
        ${foo()}
        ${foo()}
""")
        assert result_lines(t.render()) == [
            "this is foo",
            "cached:",
            "this is foo"
        ]
        
if __name__ == '__main__':
    unittest.main()
