from mako.template import Template
import unittest


class ComponentTest(unittest.TestCase):
    def test_component_noargs(self):
        template = Template("""
        
        ${mycomp()}
        
        <%component name="mycomp">
            hello mycomp ${variable}
        </%component>
        
        """)
        assert template.render(variable='hi').strip() == """hello mycomp hi"""

    def test_component_blankargs(self):
        template = Template("""
        <%component name="mycomp()">
            hello mycomp ${variable}
        </%component>

        ${mycomp()}""")
        assert template.render(variable='hi').strip() == """hello mycomp hi"""

    def test_component_args(self):
        template = Template("""
        <%component name="mycomp(a, b)">
            hello mycomp ${variable}, ${a}, ${b}
        </%component>

        ${mycomp(5, 6)}""")
        assert template.render(variable='hi', a=5, b=6).strip() == """hello mycomp hi, 5, 6"""

    def test_inter_component(self):
        """test components calling each other"""
        template = Template("""
${b()}

<%component name="a">\
im a
</%component>

<%component name="b">
im b
and heres a:  ${a()}
</%component>

<%component name="c">
im c
</%component>
        """)
        # check that "a" is declared in "b", but not in "c"
        assert "a" not in template.module.render_c.func_code.co_varnames
        assert "a" in template.module.render_b.func_code.co_varnames
        
        # then test output
        assert template.render().strip() == "im b\nand heres a:  im a"

    def test_nested_component(self):
        template = """

        ${hi()}
        
        <%component name="hi">
            hey, im hi.
            and heres ${foo()}, ${bar()}
            
            <%component name="foo">
                this is foo
            </%component>
            
            <%component name="bar">
                this is bar
            </%component>
        </%component>
"""
        t = Template(template)
        #print t.code
        print t.render()

    def test_nested_nested_component(self):
        template = """
        
        ${a()}
        <%component name="a">
            <%component name="b1">
            </%component>
            <%component name="b2">
                a_b2 ${c1()}
                <%component name="c1">
                    a_b2_c1
                </%component>
            </%component>
            <%component name="b3">
                a_b3 ${c1()}
                <%component name="c1">
                    a_b3_c1 heres x: ${x}
                    <%
                        y = 7
                    %>
                    y is ${y}
                </%component>
                <%component name="c2">
                    a_b3_c2
                    y is ${y}
                    c1 is ${c1()}
                </%component>
                ${c2()}
            </%component>
            
            ${b1()} ${b2()}  ${b3()}
        </%component>
"""

        t = Template(template)
        #print t.code
        print t.render(x=5)
        
class ExceptionTest(unittest.TestCase):
    def test_raise(self):
        template = Template("""
            <%
                raise Exception("this is a test")
            %>
    """, format_exceptions=False)
        try:
            template.render()
            assert False
        except Exception, e:
            assert str(e) == "this is a test"
    def test_handler(self):
        def handle(context, error):
            context.write("error message is " + str(error))
            return True
            
        template = Template("""
            <%
                raise Exception("this is a test")
            %>
    """, error_handler=handle)
        assert template.render().strip() == """error message is this is a test"""
        

if __name__ == '__main__':
    unittest.main()
