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
    this is the footer
</%component>
""", lookup=collection)

        print tmpl['main'].render()

    def test_multilevel_nesting(self):
        tmpl = {}
        class LocalTmplCollection(lookup.TemplateCollection):
            def get_template(self, uri):
                return tmpl[uri]
        collection = LocalTmplCollection()

        tmpl['main'] = Template("""
<%inherit file="layout"/>
main_body ${parent.footer()}
""", lookup=collection)
        
        tmpl['layout'] = Template("""
<%inherit file="general"/>
layout_body
${next.body()}
""")

        tmpl['general'] = Template("""
<%inherit file="base"/>
general_body
${next.body()}
""")
        tmpl['base'] = Template("""
base_body
${next.body()}
<%component name="footer">
    base footer
</%component>
""", lookup=collection)

        print tmpl['main'].render()


if __name__ == '__main__':
    unittest.main()
