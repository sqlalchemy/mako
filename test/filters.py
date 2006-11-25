from mako.template import Template
import unittest
from util import result_lines, flatten_result

class FilterTest(unittest.TestCase):
    def test_basic(self):
        t = Template("""
        ${x | myfilter}
""")
        print t.code
        print t.render(x="this is x", myfilter=lambda t: "MYFILTER->%s<-MYFILTER" % t)

    def test_expr(self):
        """test filters that are themselves expressions"""
        t = Template("""
        ${x | myfilter(y)}
""")
        def myfilter(y):
            return lambda x: "MYFILTER->%s<-%s" % (x, y)
        assert flatten_result(t.render(x="this is x", myfilter=myfilter, y="this is y")) == "MYFILTER->this is x<-this is y"

    def test_component(self):
        t = Template("""
            <%component name="foo" filter="myfilter">
                this is foo
            </%component>
            ${foo()}
""")
        assert flatten_result(t.render(x="this is x", myfilter=lambda t: "MYFILTER->%s<-MYFILTER" % t)) == "MYFILTER-> this is foo <-MYFILTER"

    def test_builtins(self):
        t = Template("""
            ${"this is <text>" | h}
""")
        assert flatten_result(t.render()) == "this is &lt;text&gt;"
        
        t = Template("""
            http://foo.com/arg1=${"hi! this is a string." | u}
""")
        assert flatten_result(t.render()) == "http://foo.com/arg1=hi%21+this+is+a+string."

class BufferTest(unittest.TestCase):        
    def test_buffered_component(self):
        t = Template("""
            <%component name="foo" buffered="True">
                this is foo
            </%component>
            ${"hi->" + foo() + "<-hi"}
""")
        assert flatten_result(t.render()) == "hi-> this is foo <-hi"

    def test_unbuffered_component(self):
        t = Template("""
            <%component name="foo" buffered="False">
                this is foo
            </%component>
            ${"hi->" + foo() + "<-hi"}
""")
        assert flatten_result(t.render()) == "this is foo hi-><-hi"



if __name__ == '__main__':
    unittest.main()