from mako.template import Template
import unittest

class CallTest(unittest.TestCase):
    def test_call(self):
        t = Template("""
        
        
        <%component name="foo">
            hi im foo ${body()}
        </%component>
        
        <%call expr="foo()">
            this is the body
        </%call>
        
""")
        print t.code
#        print t.render()


    def test_compound_call(self):
        t = Template("""

        <%component name="bar">
            this is bar
        </%component>
        
        <%component name="comp1">
            this comp1 should not be called
        </%component>
        
        <%component name="foo">
            foo calling comp1: ${callargs.comp1()}
            foo calling body: ${body()}
        </%component>
        
        <%call expr="foo()">
            <%component name="comp1">
                this is comp1
            </%component>
            this is the body, ${comp1()}
        </%call>
        ${bar()}

""")
        print t.code
        print t.render()

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
                    this is c: ${body()}
                </%component>
            </%component>
        ${a()}
""")
        print t.code
        print t.render()

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
                    this is c: ${body()}
                    the embedded "d" is: ${d()}
                </%component>
            </%component>
        ${a()}
""")
        print t.code
        print t.render()
        
if __name__ == '__main__':
    unittest.main()
