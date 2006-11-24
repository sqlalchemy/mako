from mako.template import Template
from mako import lookup
import unittest
from util import flatten_result

class InheritanceTest(unittest.TestCase):
    def test_basic(self):
        tmpl = {}
        class LocalTmplCollection(lookup.TemplateCollection):
            def get_template(self, uri):
                return tmpl[uri]
        collection = LocalTmplCollection()

        tmpl['main'] = Template("""
<%inherit file="base"/>

<%component name="header">
    main header.
</%component>

this is the content.
""", lookup=collection)

        tmpl['base'] = Template("""
This is base.

header: ${self.header()}

body: ${self.body()}

footer: ${self.footer()}

<%component name="footer">
    this is the footer. header again ${next.header()}
</%component>
""", lookup=collection)

        print tmpl['main'].render()

    def test_multilevel_nesting(self):
        collection = lookup.TemplateLookup()

        collection.put_string('main', """
<%inherit file="layout"/>
<%component name="d">main_d</%component>
main_body ${parent.d()}
full stack from the top:
    ${self.name} ${parent.name} ${parent.context['parent'].name} ${parent.context['parent'].context['parent'].name}
""")
        
        collection.put_string('layout', """
<%inherit file="general"/>
<%component name="d">layout_d</%component>
layout_body
parent name: ${parent.name}
${parent.d()}
${parent.context['parent'].d()}
${next.body()}
""")

        collection.put_string('general', """
<%inherit file="base"/>
<%component name="d">general_d</%component>
general_body
 % if next is UNDEFINED:
    next is undefined !
 % else:
${next.d()}
${next.context['next'].d()}
${next.body()}
 % endif
""")
        collection.put_string('base', """
base_body
full stack from the base:
    ${self.name} ${self.context['parent'].name} ${self.context['parent'].context['parent'].name} ${self.context['parent'].context['parent'].context['parent'].name}
${next.body()}
<%component name="d">base_d</%component>
""")

        print collection.get_template('main').render()

    def test_includes(self):
        collection = lookup.TemplateLookup()
        
        collection.put_string("base", """
        <html>
            <%component name="a">base_a</%component>
            This is the base.
            ${next.body()}
        </html>
""")

        collection.put_string("index","""
        <%inherit file="base"/>
        this is index.
        a is: ${self.a()}
        
        <%include file="secondary"/>
""")

        collection.put_string("secondary","""
        <%inherit file="base"/>
        this is secondary.
        a is: ${self.a()}
""")

        print collection.get_template("index").render()

    def test_namespaces(self):
        """test that templates used via <%namespace> have access to an inheriting 'self', and that
        the full 'self' is also exported."""
        collection = lookup.TemplateLookup()
        
        collection.put_string("base", """
        <html>
            <%component name="a">base_a</%component>
            <%component name="b">base_b</%component>
            This is the base.
            ${next.body()}
        </html>
""")

        collection.put_string("layout", """
        <html>
            <%inherit file="base"/>
            <%component name="a">layout_a</%component>
            This is the layout..
            ${next.body()}
        </html>
""")

        collection.put_string("index","""
        <%inherit file="base"/>
        <%namespace name="sc" file="secondary"/>
        this is index.
        a is: ${self.a()}
        sc.a is: ${sc.a()}
        sc.b is: ${sc.b()}
""")

        collection.put_string("secondary","""
        <%inherit file="layout"/>
        <%component name="c">secondary_c.  a is ${self.a()} b is ${self.b()}</%component>
        this is secondary.
        a is: ${self.a()}
""")
        print collection.get_template('index').render()
        
if __name__ == '__main__':
    unittest.main()
