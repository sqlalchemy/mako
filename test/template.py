# -*- encoding: utf-8 -*-

from mako.template import Template
import unittest
from util import flatten_result, result_lines

class EncodingTest(unittest.TestCase):
    def test_unicode(self):
        template = Template(u"""Alors vous imaginez ma surprise, au lever du jour, quand une drôle de petit voix m’a réveillé. Elle disait: « S’il vous plaît… dessine-moi un mouton! »""")
        assert template.render_unicode() == u"""Alors vous imaginez ma surprise, au lever du jour, quand une drôle de petit voix m’a réveillé. Elle disait: « S’il vous plaît… dessine-moi un mouton! »"""
        
    def test_unicode_arg(self):
        val = u"""Alors vous imaginez ma surprise, au lever du jour, quand une drôle de petit voix m’a réveillé. Elle disait: « S’il vous plaît… dessine-moi un mouton! »"""
        template = Template("${val}")
        assert template.render_unicode(val=val) == u"""Alors vous imaginez ma surprise, au lever du jour, quand une drôle de petit voix m’a réveillé. Elle disait: « S’il vous plaît… dessine-moi un mouton! »"""

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
        
if __name__ == '__main__':
    unittest.main()
