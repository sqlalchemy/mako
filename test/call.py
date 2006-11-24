from mako.template import Template
import unittest
from util import result_lines

class CallTest(unittest.TestCase):
    def test_call(self):
        t = Template("""
        <%component name="foo">
            hi im foo ${caller.body(y=5)}
        </%component>
        
        <%call expr="foo()">
            this is the body, y is ${y}
        </%call>
""")
        assert result_lines(t.render()) == ['hi im foo', 'this is the body, y is 5']


    def test_compound_call(self):
        t = Template("""

        <%component name="bar">
            this is bar
        </%component>
        
        <%component name="comp1">
            this comp1 should not be called
        </%component>
        
        <%component name="foo">
            foo calling comp1: ${caller.comp1(x=5)}
            foo calling body: ${caller.body()}
        </%component>
        
        <%call expr="foo()">
            <%component name="comp1(x)">
                this is comp1, ${x}
            </%component>
            this is the body, ${comp1(6)}
        </%call>
        ${bar()}

""")
        assert result_lines(t.render()) == ['foo calling comp1:', 'this is comp1, 5', 'foo calling body:', 'this is the body,', 'this is comp1, 6', 'this is bar']

    def test_multi_call(self):
        t = Template("""
            <%component name="a">
                this is a. 
                <%call expr="b()">
                    this is a's ccall.  heres my body: ${caller.body()}
                </%call>
            </%component>
            <%component name="b">
                this is b.  heres  my body: ${caller.body()}
                whats in the body's caller's body ? ${caller.context['caller'].body()}
            </%component>
            
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

    def test_multi_call_in_nested(self):
        t = Template("""
            <%component name="embedded">
            <%component name="a">
                this is a. 
                <%call expr="b()">
                    this is a's ccall.  heres my body: ${caller.body()}
                </%call>
            </%component>
            <%component name="b">
                this is b.  heres  my body: ${caller.body()}
                whats in the body's caller's body ? ${caller.context['caller'].body()}
            </%component>

            <%call expr="a()">
                heres the main templ call
            </%call>
            </%component>
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
            <%component name="a">
                this is a ${b()}
                <%component name="b">
                    this is b
                    <%call expr="c()">
                        this is the body in b's call
                    </%call>
                </%component>
                <%component name="c">
                    this is c: ${caller.body()}
                </%component>
            </%component>
        ${a()}
""")
        assert result_lines(t.render()) == ['this is a', 'this is b', 'this is c:', "this is the body in b's call"]

    def test_call_in_nested_2(self):
        t = Template("""
            <%component name="a">
                <%component name="d">
                    not this d
                </%component>
                this is a ${b()}
                <%component name="b">
                    <%component name="d">
                        not this d either
                    </%component>
                    this is b
                    <%call expr="c()">
                        <%component name="d">
                            this is d
                        </%component>
                        this is the body in b's call
                    </%call>
                </%component>
                <%component name="c">
                    this is c: ${caller.body()}
                    the embedded "d" is: ${caller.d()}
                </%component>
            </%component>
        ${a()}
""")
        assert result_lines(t.render()) == ['this is a', 'this is b', 'this is c:', "this is the body in b's call", 'the embedded "d" is:', 'this is d']
        
if __name__ == '__main__':
    unittest.main()
