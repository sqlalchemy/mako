from mako.template import Template
import unittest, re

class NamespaceTest(unittest.TestCase):
    def test_inline(self):
        template = """
        <%namespace name="x">
            <%component name="a">
                this is x a
            </%component>
            <%component name="b">
                this is x b, and heres ${a()}
            </%component>
        </%namespace>
        
        ${x.a()}
        
        ${x.b()}
"""
        t = Template(template)
        result = t.render()
        result = re.sub(r'[\s\n]+', ' ', result).strip()
        assert result == "this is x a this is x b, and heres this is x a"


if __name__ == '__main__':
    unittest.main()
