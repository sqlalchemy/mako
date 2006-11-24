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
${next.d()}
${next.context['next'].d()}
${next.body()}
""")
        collection.put_string('base', """
base_body
full stack from the base:
    ${self.name} ${self.context['parent'].name} ${self.context['parent'].context['parent'].name} ${self.context['parent'].context['parent'].context['parent'].name}
${next.body()}
<%component name="d">base_d</%component>
""")

        print collection.get_template('main').render()


if __name__ == '__main__':
    unittest.main()
