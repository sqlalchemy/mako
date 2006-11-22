from mako.template import Template
from mako import lookup
import unittest
from util import flatten_result

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
        assert flatten_result(template.render()) == "im b and heres a: im a"

class ScopeTest(unittest.TestCase):
    """test scoping rules.  The key is, enclosing scope always takes precedence over contextual scope."""
    def test_scope_one(self):
        t = Template("""
        <%component name="a">
            this is a, and y is ${y}
        </%component>

        ${a()}

        <%
            y = 7
        %>

        ${a()}

""")
        assert flatten_result(t.render(y=None)) == "this is a, and y is None this is a, and y is 7"

    def test_scope_two(self):
        t = Template("""
        y is ${y}

        <%
            y = 7
        %>

        y is ${y}
""")
        try:
            t.render(y=None)
            assert False
        except UnboundLocalError:
            assert True

    def test_scope_four(self):
        """test that variables are pulled from 'enclosing' scope before context."""
        t = Template("""
            <%
                x = 5
            %>
            <%component name="a">
                this is a. x is ${x}.
            </%component>
            
            <%component name="b">
                <%
                    x = 9
                %>
                this is b. x is ${x}.
                calling a. ${a()}
            </%component>
        
            ${b()}
""")
        assert flatten_result(t.render()) == "this is b. x is 9. calling a. this is a. x is 5."
    
    def test_scope_five(self):
        """test that variables are pulled from 'enclosing' scope before context."""
        # same as test four, but adds a scope around it.
        t = Template("""
            <%component name="enclosing">
            <%
                x = 5
            %>
            <%component name="a">
                this is a. x is ${x}.
            </%component>

            <%component name="b">
                <%
                    x = 9
                %>
                this is b. x is ${x}.
                calling a. ${a()}
            </%component>

            ${b()}
            </%component>
            ${enclosing()}
""")
        assert flatten_result(t.render()) == "this is b. x is 9. calling a. this is a. x is 5."

    def test_scope_six(self):
        """test that the initial context counts as 'enclosing' scope, for plain components"""
        t = Template("""

        <%component name="a">
            a: x is ${x}
        </%component>

        <%component name="b">
            <%
                x = 10
            %>
            b. x is ${x}.  ${a()}
        </%component>

        ${b()}
    """)
        assert flatten_result(t.render(x=5)) == "b. x is 10. a: x is 5"

    def test_scope_seven(self):
        """test that the initial context counts as 'enclosing' scope, for nested components"""
        t = Template("""
        <%component name="enclosing">
            <%component name="a">
                a: x is ${x}
            </%component>

            <%component name="b">
                <%
                    x = 10
                %>
                b. x is ${x}.  ${a()}
            </%component>

            ${b()}
        </%component>
        ${enclosing()}
    """)
        assert flatten_result(t.render(x=5)) == "b. x is 10. a: x is 5"

    def test_scope_eight(self):
        """test that the initial context counts as 'enclosing' scope, for nested components"""
        t = Template("""
        <%component name="enclosing">
            <%component name="a">
                a: x is ${x}
            </%component>

            <%component name="b">
                <%
                    x = 10
                    context['x'] = x
                %>
                
                b. x is ${x}.  ${a()}
            </%component>

            ${b()}
        </%component>
        ${enclosing()}
    """)
        assert flatten_result(t.render(x=5)) == "b. x is 10. a: x is 10"

    def test_scope_nine(self):
        """test that 'enclosing scope' doesnt get exported to other templates"""
        tmpl = {}
        class LocalTmplCollection(lookup.TemplateCollection):
            def get_template(self, uri):
                return tmpl[uri]
        collection = LocalTmplCollection()
        
        tmpl['main'] = Template("""
        <%
            x = 5
        %>
        this is main.  <%include file="secondary"/>
""", lookup=collection)

        tmpl['secondary'] = Template("""
        this is secondary.  x is ${x}
""", lookup=collection)

        assert flatten_result(tmpl['main'].render(x=2)) == "this is main. this is secondary. x is 2"
        
    def test_scope_ten(self):
        t = Template("""
            <%component name="a">
                <%component name="b">
                    <%
                        y = 19
                    %>
                    b/c: ${c()}
                    b/y: ${y}
                </%component>
                <%component name="c">
                    c/y: ${y}
                </%component>

                <%
                    # we assign to "y".  but the 'enclosing scope' of "b" and "c" is from the "y" on the outside
                    y = 10
                %>
                a/y: ${y}
                a/b: ${b()}
            </%component>

            <%
                y = 7
            %>
            main/a: ${a()}
            main/y: ${y}
    """)
        assert flatten_result(t.render()) == "main/a: a/y: 10 a/b: b/c: c/y: 10 b/y: 19 main/y: 7"

    def test_unbound_scope(self):
        t = Template("""
            <%
                y = 10
            %>
            <%component name="a">
                y is: ${y}
                <%
                    # should raise error ?
                    y = 15
                %>
                y is ${y}
            </%component>
            ${a()}
""")
        try:
            print t.render()
            assert False
        except UnboundLocalError:
            assert True

    def test_unbound_scope_two(self):
        t = Template("""
            <%component name="enclosing">
            <%
                y = 10
            %>
            <%component name="a">
                y is: ${y}
                <%
                    # should raise error ?
                    y = 15
                %>
                y is ${y}
            </%component>
            ${a()}
            </%component>
            ${enclosing()}
""")
        try:
            print t.render()
            assert False
        except UnboundLocalError:
            assert True
        
class NestedComponentTest(unittest.TestCase):
    def test_nested_component(self):
        t = Template("""

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
""")
        assert flatten_result(t.render()) == "hey, im hi. and heres this is foo , this is bar"

    def test_nested_with_args(self):
        t = Template("""
        ${a()}
        <%component name="a">
            <%component name="b(x, y=2)">
                b x is ${x} y is ${y}
            </%component>
            a ${b(5)}
        </%component>
""")
        assert flatten_result(t.render()) == "a b x is 5 y is 2"
        
    def test_nested_component_2(self):
        template = Template("""
        ${a()}
        <%component name="a">
            <%component name="b">
                <%component name="c">
                    comp c
                </%component>
                ${c()}
            </%component>
            ${b()}
        </%component>
""")
        assert flatten_result(template.render()) == "comp c"

    def test_nested_nested_component(self):
        t = Template("""
        
        ${a()}
        <%component name="a">
            a
            <%component name="b1">
                a_b1
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
""")
        assert flatten_result(t.render(x=5, y=None)) == "a a_b1 a_b2 a_b2_c1 a_b3 a_b3_c1 heres x: 5 y is 7 a_b3_c2 y is None c1 is a_b3_c1 heres x: 5 y is 7"
    
    def test_nested_nested_component_2(self):
        t = Template("""
        <%component name="a">
            this is a ${b()}
            <%component name="b">
                this is b
                ${c()}
            </%component>
            
            <%component name="c">
                this is c
            </%component>
        </%component>
        ${a()}
""" )
        assert flatten_result(t.render()) == "this is a this is b this is c"

    def test_outer_scope(self):
        t = Template("""
        <%component name="a">
            a: x is ${x}
        </%component>

        <%component name="b">
            <%component name="c">
            <%
                x = 10
            %>
            c. x is ${x}.  ${a()}
            </%component>
            
            b. ${c()}
        </%component>

        ${b()}
        
        x is ${x}
""")
        assert flatten_result(t.render(x=5)) == "b. c. x is 10. a: x is 5 x is 5"
            
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
