from mako.template import Template
import unittest
from util import result_lines

class FilterTest(unittest.TestCase):
    def test_basic(self):
        t = Template("""
        ${x | myfilter}
""")
        print t.code
        print t.render(x="this is x", myfilter=lambda t: "MYFILTER->%s<-MYFILTER" % t)
    def test_component(self):
        t = Template("""
            <%component name="foo" filter="myfilter">
                this is foo
            </%component>
            ${foo()}
""")
        print t.code
        print t.render(x="this is x", myfilter=lambda t: "MYFILTER->%s<-MYFILTER" % t)
if __name__ == '__main__':
    unittest.main()