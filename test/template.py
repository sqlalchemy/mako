# -*- coding: utf-8 -*-

from mako.template import Template
from mako.lookup import TemplateLookup
import unittest, re, os
from util import flatten_result, result_lines

if not os.access('./test_htdocs', os.F_OK):
    os.mkdir('./test_htdocs')
if not os.access('./test_htdocs/subdir', os.F_OK):
    os.mkdir('./test_htdocs/subdir')
file('./test_htdocs/unicode.html', 'w').write("""# -*- coding: utf-8 -*-
Alors vous imaginez ma surprise, au lever du jour, quand une drôle de petit voix m’a réveillé. Elle disait: « S’il vous plaît… dessine-moi un mouton! »""")
    
class EncodingTest(unittest.TestCase):
    def test_unicode(self):
        template = Template(u"""Alors vous imaginez ma surprise, au lever du jour, quand une drôle de petit voix m’a réveillé. Elle disait: « S’il vous plaît… dessine-moi un mouton! »""")
        assert template.render_unicode() == u"""Alors vous imaginez ma surprise, au lever du jour, quand une drôle de petit voix m’a réveillé. Elle disait: « S’il vous plaît… dessine-moi un mouton! »"""
        
    def test_unicode_arg(self):
        val = u"""Alors vous imaginez ma surprise, au lever du jour, quand une drôle de petit voix m’a réveillé. Elle disait: « S’il vous plaît… dessine-moi un mouton! »"""
        template = Template("${val}")
        assert template.render_unicode(val=val) == u"""Alors vous imaginez ma surprise, au lever du jour, quand une drôle de petit voix m’a réveillé. Elle disait: « S’il vous plaît… dessine-moi un mouton! »"""

    def test_unicode_file(self):
        template = Template(filename='./test_htdocs/unicode.html', module_directory='./test_htdocs')
        assert template.render_unicode() == u"""Alors vous imaginez ma surprise, au lever du jour, quand une drôle de petit voix m’a réveillé. Elle disait: « S’il vous plaît… dessine-moi un mouton! »"""

    def test_unicode_memory(self):
        val = u"""Alors vous imaginez ma surprise, au lever du jour, quand une drôle de petit voix m’a réveillé. Elle disait: « S’il vous plaît… dessine-moi un mouton! »"""
        val = "# -*- coding: utf-8 -*-\n" + val.encode('utf-8')
        template = Template(val)
        assert template.render_unicode() == u"""Alors vous imaginez ma surprise, au lever du jour, quand une drôle de petit voix m’a réveillé. Elle disait: « S’il vous plaît… dessine-moi un mouton! »"""

    def test_unicode_literal_in_expr(self):
        template = Template(u"""# -*- coding: utf-8 -*-
        ${u"Alors vous imaginez ma surprise, au lever du jour, quand une drôle de petit voix m’a réveillé. Elle disait: « S’il vous plaît… dessine-moi un mouton! »"}
        """.encode('utf-8'))
        assert template.render_unicode().strip() == u"""Alors vous imaginez ma surprise, au lever du jour, quand une drôle de petit voix m’a réveillé. Elle disait: « S’il vous plaît… dessine-moi un mouton! »"""

    def test_unicode_literal_in_code(self):
        template = Template(u"""# -*- coding: utf-8 -*-
        <%
            context.write(u"Alors vous imaginez ma surprise, au lever du jour, quand une drôle de petit voix m’a réveillé. Elle disait: « S’il vous plaît… dessine-moi un mouton! »")
        %>
        """.encode('utf-8'))
        assert template.render_unicode().strip() == u"""Alors vous imaginez ma surprise, au lever du jour, quand une drôle de petit voix m’a réveillé. Elle disait: « S’il vous plaît… dessine-moi un mouton! »"""

    def test_unicode_literal_in_controlline(self):
        template = Template(u"""# -*- coding: utf-8 -*-
        <%
            x = u"drôle de petit voix m’a réveillé."
        %>
        % if x==u"drôle de petit voix m’a réveillé.":
            hi, ${x}
        % endif
        """.encode('utf-8'))
        assert template.render_unicode().strip() == u"""hi, drôle de petit voix m’a réveillé."""
    
    def test_input_encoding(self):
        """test the 'input_encoding' flag on Template, and that unicode objects arent double-decoded"""
        s2 = u"hello ${f(u'śląsk')}"
        res = Template(s2, input_encoding='utf-8').render_unicode(f=lambda x:x)
        assert res == u"hello śląsk"

        s2 = u"# -*- coding: utf-8 -*-\nhello ${f(u'śląsk')}"
        res = Template(s2).render_unicode(f=lambda x:x)
        assert res == u"hello śląsk"

            
    def test_encoding(self):
        val = u"""Alors vous imaginez ma surprise, au lever du jour, quand une drôle de petit voix m’a réveillé. Elle disait: « S’il vous plaît… dessine-moi un mouton! »"""
        template = Template(val, output_encoding='utf-8')
        assert template.render() == val.encode('utf-8')
    
    def test_read_unicode(self):
        lookup = TemplateLookup(directories=['./test_htdocs'], filesystem_checks=True, output_encoding='utf-8')
        template = lookup.get_template('/read_unicode.html')
        data = template.render(path=os.path.join('./test_htdocs', 'internationalization.html'))
        

class PageArgsTest(unittest.TestCase):
    def test_basic(self):
        template = Template("""
            <%page args="x, y, z=7"/>
            
            this is page, ${x}, ${y}, ${z}
""")

        assert flatten_result(template.render(x=5, y=10)) == "this is page, 5, 10, 7"
        assert flatten_result(template.render(x=5, y=10, z=32)) == "this is page, 5, 10, 32"
        try:
            template.render(y=10)
            assert False
        except TypeError, e:
            assert True

    def test_with_context(self):
        template = Template("""
            <%page args="x, y, z=7"/>

            this is page, ${x}, ${y}, ${z}, ${w}
""")

        assert flatten_result(template.render(x=5, y=10, w=17)) == "this is page, 5, 10, 7, 17"

    def test_overrides_builtins(self):
        template = Template("""
            <%page args="id"/>
            
            this is page, id is ${id}
        """)
        
        assert flatten_result(template.render(id="im the id")) == "this is page, id is im the id"
        

        
class ControlTest(unittest.TestCase):
    def test_control(self):
        t = Template("""
    # this is a template.
    % for x in y:
    %   if x.has_key('test'):
        yes x has test
    %   else:
        no x does not have test
    %endif
    %endfor
""")
        assert result_lines(t.render(y=[{'test':'one'}, {'foo':'bar'}, {'foo':'bar', 'test':'two'}])) == [
            "yes x has test",
            "no x does not have test",
            "yes x has test"
        ]

class GlobalsTest(unittest.TestCase):
    def test_globals(self):
        t= Template("""
            <%!
                y = "hi"
            %>
        y is ${y}
""")
        assert t.render().strip() == "y is hi"


class ModuleDirTest(unittest.TestCase):
    def test_basic(self):
        file('./test_htdocs/modtest.html', 'w').write("""this is a test""")
        file('./test_htdocs/subdir/modtest.html', 'w').write("""this is a test""")
        t = Template(filename='./test_htdocs/modtest.html', module_directory='./test_htdocs/modules')
        t2 = Template(filename='./test_htdocs/subdir/modtest.html', module_directory='./test_htdocs/modules')
        assert t.module.__file__ == os.path.normpath('./test_htdocs/modules/test_htdocs/modtest.html.py')
        assert t2.module.__file__ == os.path.normpath('./test_htdocs/modules/test_htdocs/subdir/modtest.html.py')
    def test_callable(self):
        file('./test_htdocs/modtest.html', 'w').write("""this is a test""")
        file('./test_htdocs/subdir/modtest.html', 'w').write("""this is a test""")
        def get_modname(filename, uri):
            return os.path.dirname(filename) + "/foo/" + os.path.basename(filename) + ".py"
        lookup = TemplateLookup('./test_htdocs', modulename_callable=get_modname)
        t = lookup.get_template('/modtest.html')
        t2 = lookup.get_template('/subdir/modtest.html')
        assert t.module.__file__ == 'test_htdocs/foo/modtest.html.py'
        assert t2.module.__file__ == 'test_htdocs/subdir/foo/modtest.html.py'
        
            
if __name__ == '__main__':
    unittest.main()
