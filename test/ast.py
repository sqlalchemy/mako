import unittest

from mako import ast, util, exceptions
from compiler import parse

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
        parsed = ast.PythonCode(code, 0, 0, None)
        assert parsed.declared_identifiers == util.Set(['a','b','c', 'g', 'h', 'i', 'u', 'k', 'j', 'gh', 'lar', 'x'])
        assert parsed.undeclared_identifiers == util.Set(['x', 'q', 'foo', 'gah', 'blah'])
    
        parsed = ast.PythonCode("x + 5 * (y-z)", 0, 0, None)
        assert parsed.undeclared_identifiers == util.Set(['x', 'y', 'z'])
        assert parsed.declared_identifiers == util.Set()

    def test_locate_identifiers_2(self):
        code = """
import foobar
from lala import hoho, yaya
import bleep as foo
result = []
data = get_data()
for x in data:
    result.append(x+7)
"""
        parsed = ast.PythonCode(code, 0, 0, None)
        assert parsed.undeclared_identifiers == util.Set(['get_data'])
        assert parsed.declared_identifiers == util.Set(['result', 'data', 'x', 'hoho', 'foobar', 'foo', 'yaya'])

    def test_locate_identifiers_3(self):
        """test that combination assignment/expressions of the same identifier log the ident as 'undeclared'"""
        code = """
x = x + 5
for y in range(1, y):
    print "hi"
[z for z in range(1, z)]
(q for q in range (1, q))
"""
        parsed = ast.PythonCode(code, 0, 0, None)
        assert parsed.undeclared_identifiers == util.Set(['x', 'y', 'z', 'q'])
    
    def test_locate_identifiers_4(self):
        code = """
x = 5
print y
def mydef(mydefarg):
    print "mda is", mydefarg
"""    
        parsed = ast.PythonCode(code, 0, 0, None)
        assert parsed.undeclared_identifiers == util.Set(['y'])
        assert parsed.declared_identifiers == util.Set(['mydef', 'x'])
    
    def test_locate_identifiers_5(self):
        code = """
try:
    print x
except:
    print y
"""
        parsed = ast.PythonCode(code, 0, 0, None)
        assert parsed.undeclared_identifiers == util.Set(['x', 'y'])
    
    def test_locate_identifiers_6(self):
        code = """
def foo():
    return bar()
"""
        parsed = ast.PythonCode(code, 0, 0, None)
        assert parsed.undeclared_identifiers == util.Set(['bar'])
    
        code = """
def lala(x, y):
    return x, y, z
print x
"""
        parsed = ast.PythonCode(code, 0, 0, None)
        assert parsed.undeclared_identifiers == util.Set(['z', 'x'])
        assert parsed.declared_identifiers == util.Set(['lala'])
    
        code = """
def lala(x, y):
    def hoho():
        def bar():
            z = 7
print z
"""
        parsed = ast.PythonCode(code, 0, 0, None)
        assert parsed.undeclared_identifiers == util.Set(['z'])
        assert parsed.declared_identifiers == util.Set(['lala'])

    def test_no_global_imports(self):
        code = """
from foo import *
import x as bar
"""
        try:
            parsed = ast.PythonCode(code, 0, 0, None)
            assert False
        except exceptions.CompileException, e:
            assert str(e).startswith("'import *' is not supported")
            
    def test_python_fragment(self):
        parsed = ast.PythonFragment("for x in foo:", 0, 0, None)
        assert parsed.declared_identifiers == util.Set(['x'])
        assert parsed.undeclared_identifiers == util.Set(['foo'])
        
        parsed = ast.PythonFragment("try:", 0, 0, None)

        parsed = ast.PythonFragment("except MyException, e:", 0, 0, None)
        assert parsed.declared_identifiers == util.Set(['e'])
        assert parsed.undeclared_identifiers == util.Set(['MyException'])
    
    def test_argument_list(self):
        parsed = ast.ArgumentList("3, 5, 'hi', x+5, context.get('lala')", 0, 0, None)
        assert parsed.undeclared_identifiers == util.Set(['x', 'context'])
        assert [x for x in parsed.args] == ["3", "5", "'hi'", "(x + 5)", "context.get('lala')"]

        parsed = ast.ArgumentList("h", 0, 0, None)
        assert parsed.args == ["h"]

    def test_function_decl(self):
        """test getting the arguments from a function"""
        code = "def foo(a, b, c=None, d='hi', e=x, f=y+7):pass"
        parsed = ast.FunctionDecl(code, 0, 0, None)
        assert parsed.funcname=='foo'
        assert parsed.argnames==['a', 'b', 'c', 'd', 'e', 'f']

    def test_function_decl_2(self):
        """test getting the arguments from a function"""
        code = "def foo(a, b, c=None, *args, **kwargs):pass"
        parsed = ast.FunctionDecl(code, 0, 0, None)
        assert parsed.funcname=='foo'
        assert parsed.argnames==['a', 'b', 'c', 'args', 'kwargs']
    
    def test_expr_generate(self):
        """test the round trip of expressions to AST back to python source"""
        x = 1
        y = 2
        class F(object):
            def bar(self, a,b):
                return a + b
        def lala(arg):
            return "blah" + arg
        local_dict = dict(x=x, y=y, foo=F(), lala=lala)
        
        code = "str((x+7*y) / foo.bar(5,6)) + lala('ho')"
        astnode = parse(code)
        newcode = ast.ExpressionGenerator(astnode).value()
        #print "newcode:" + newcode
        #print "result:" + eval(code, local_dict)
        assert (eval(code, local_dict) == eval(newcode, local_dict))
        
        a = ["one", "two", "three"]
        hoho = {'somevalue':"asdf"}
        g = [1,2,3,4,5]
        local_dict = dict(a=a,hoho=hoho,g=g)
        code = "a[2] + hoho['somevalue'] + repr(g[3:5]) + repr(g[3:]) + repr(g[:5])"
        astnode = parse(code)
        newcode = ast.ExpressionGenerator(astnode).value()
        #print newcode
        #print "result:", eval(code, local_dict)
        assert(eval(code, local_dict) == eval(newcode, local_dict))
        
        local_dict={'f':lambda :9, 'x':7}
        code = "x+f()"
        astnode = parse(code)
        newcode = ast.ExpressionGenerator(astnode).value()
        assert(eval(code, local_dict)) == eval(newcode, local_dict)

        for code in ["repr({'x':7,'y':18})", "repr([])", "repr({})", "repr([{3:[]}])", "repr({'x':37*2 + len([6,7,8])})", "repr([1, 2, {}, {'x':'7'}])", "repr({'x':-1})", "repr(((1,2,3), (4,5,6)))", "repr(1 and 2 and 3 and 4)", "repr(True and False or 55)", "repr(1 & 2 | 3)", "repr(3//5)", "repr(3^5)", "repr([q.endswith('e') for q in ['one', 'two', 'three']])", "repr([x for x in (5,6,7) if x == 6])", "repr(not False)"]:
            local_dict={}
            astnode = parse(code)
            newcode = ast.ExpressionGenerator(astnode).value()
            print code, newcode
            assert(eval(code, local_dict)) == eval(newcode, local_dict), "%s != %s" % (code, newcode)

if __name__ == '__main__':
    unittest.main()
    
    