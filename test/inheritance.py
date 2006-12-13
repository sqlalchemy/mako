from mako.template import Template
from mako import lookup
import unittest
from util import flatten_result, result_lines

class InheritanceTest(unittest.TestCase):
    def test_basic(self):
        collection = lookup.TemplateLookup()

        collection.put_string('main', """
<%inherit file="base"/>

<%def name="header()">
    main header.
</%def>

this is the content.
""")

        collection.put_string('base', """
This is base.

header: ${self.header()}

body: ${self.body()}

footer: ${self.footer()}

<%def name="footer()">
    this is the footer. header again ${next.header()}
</%def>
""")

        assert result_lines(collection.get_template('main').render()) == [
            'This is base.',
             'header:',
             'main header.',
             'body:',
             'this is the content.',
             'footer:',
             'this is the footer. header again',
             'main header.'
        ]

    def test_multilevel_nesting(self):
        collection = lookup.TemplateLookup()

        collection.put_string('main', """
<%inherit file="layout"/>
<%def name="d()">main_d</%def>
main_body ${parent.d()}
full stack from the top:
    ${self.name} ${parent.name} ${parent.context['parent'].name} ${parent.context['parent'].context['parent'].name}
""")
        
        collection.put_string('layout', """
<%inherit file="general"/>
<%def name="d()">layout_d</%def>
layout_body
parent name: ${parent.name}
${parent.d()}
${parent.context['parent'].d()}
${next.body()}
""")

        collection.put_string('general', """
<%inherit file="base"/>
<%def name="d()">general_d</%def>
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
<%def name="d()">base_d</%def>
""")

        assert result_lines(collection.get_template('main').render()) == [
            'base_body',
             'full stack from the base:',
             'self:main self:layout self:general self:base',
             'general_body',
             'layout_d',
             'main_d',
             'layout_body',
             'parent name: self:general',
             'general_d',
             'base_d',
             'main_body layout_d',
             'full stack from the top:',
             'self:main self:layout self:general self:base'
        ]
        
    def test_includes(self):
        """test that an included template also has its full hierarchy invoked."""
        collection = lookup.TemplateLookup()
        
        collection.put_string("base", """
        <%def name="a()">base_a</%def>
        This is the base.
        ${next.body()}
        End base.
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

        assert result_lines(collection.get_template("index").render()) == [
            'This is the base.', 
            'this is index.',
             'a is: base_a',
             'This is the base.',
             'this is secondary.',
             'a is: base_a',
             'End base.',
             'End base.'
            ]

    def test_namespaces(self):
        """test that templates used via <%namespace> have access to an inheriting 'self', and that
        the full 'self' is also exported."""
        collection = lookup.TemplateLookup()
        
        collection.put_string("base", """
        <%def name="a()">base_a</%def>
        <%def name="b()">base_b</%def>
        This is the base.
        ${next.body()}
""")

        collection.put_string("layout", """
        <%inherit file="base"/>
        <%def name="a()">layout_a</%def>
        This is the layout..
        ${next.body()}
""")

        collection.put_string("index","""
        <%inherit file="base"/>
        <%namespace name="sc" file="secondary"/>
        this is index.
        a is: ${self.a()}
        sc.a is: ${sc.a()}
        sc.b is: ${sc.b()}
        sc.c is: ${sc.c()}
        sc.body is: ${sc.body()}
""")

        collection.put_string("secondary","""
        <%inherit file="layout"/>
        <%def name="c()">secondary_c.  a is ${self.a()} b is ${self.b()} d is ${self.d()}</%def>
        <%def name="d()">secondary_d.</%def>
        this is secondary.
        a is: ${self.a()}
        c is: ${self.c()}
""")

        assert result_lines(collection.get_template('index').render()) ==  ['This is the base.',
         'this is index.',
         'a is: base_a',
         'sc.a is: layout_a',
         'sc.b is: base_b',
         'sc.c is: secondary_c. a is layout_a b is base_b d is secondary_d.',
         'sc.body is:',
         'this is secondary.',
         'a is: layout_a',
         'c is: secondary_c. a is layout_a b is base_b d is secondary_d.'
         ]

    def test_dynamic(self):
        collection = lookup.TemplateLookup()
        collection.put_string("base", """
            this is the base.
            ${next.body()}
        """)
        collection.put_string("index", """
            <%!
                def dyn(context):
                    if context.get('base', None) is not None:
                        return 'base'
                    else:
                        return None
            %>
            <%inherit file="${dyn(context)}"/>
            this is index.
        """)
        assert result_lines(collection.get_template('index').render()) == [
            'this is index.'
        ]
        assert result_lines(collection.get_template('index').render(base=True)) == [
            'this is the base.',
            'this is index.'
        ]
if __name__ == '__main__':
    unittest.main()
