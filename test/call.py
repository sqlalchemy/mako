from mako.template import Template
import unittest

class TestCall(unittest.TestCase):
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
        
        <%component name="foo">
            hi im foo ${body()}
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
        
if __name__ == '__main__':
    unittest.main()
