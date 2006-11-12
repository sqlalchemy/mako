import unittest

from mako import ast, util

class AstParseTest(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    def test_locate_identifiers(self):
        """test the location of identifiers in a python code string"""
        code = """
a = 10
b = 5
c = x * 5 + a + b + q
(g,h,i) = (1,2,3)
[u,k,j] = [4,5,6]
foo.hoho.lala.bar = 7 + gah.blah + u + blah
for lar in (1,2,3):
    gh = 5
    x = 12
print "hello world, ", a, b
print "Another expr", c
"""
        parsed = ast.PythonCode(code)
        assert parsed.declared_identifiers == util.Set(['a','b','c', 'g', 'h', 'i', 'u', 'k', 'j', 'gh', 'lar'])
        assert parsed.undeclared_identifiers == util.Set(['x', 'q', 'foo', 'gah', 'blah'])
    
        parsed = ast.PythonCode("x + 5 * (y-z)")
        assert parsed.undeclared_identifiers == util.Set(['x', 'y', 'z'])
        assert parsed.declared_identifiers == util.Set()
    
if __name__ == '__main__':
    unittest.main()
    
    