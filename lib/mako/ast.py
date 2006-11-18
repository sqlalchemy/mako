"""utilities for analyzing expressions and blocks of Python code, as well as generating Python from AST nodes"""

from compiler import ast, parse, visitor
from mako import util, exceptions
from StringIO import StringIO
import re

class PythonCode(object):
    """represents information about a string containing Python code"""
    def __init__(self, code, lineno, pos):
        self.code = code
        self.declared_identifiers = util.Set()
        self.undeclared_identifiers = util.Set()

        expr = parse(code, "exec")
        class FindIdentifiers(object):
            def visitAssName(s, node, *args):
                if node.name not in self.undeclared_identifiers:
                    self.declared_identifiers.add(node.name)
            def visitTryExcept(s, node, *args):
                for (decl, s2, s3) in node.handlers:
                    if decl is not None:
                        (exception, ident) = [n.name for n in decl.nodes]
                        self.declared_identifiers.add(ident)
            def visitName(s, node, *args):
                if node.name not in __builtins__ and node.name not in self.declared_identifiers:
                    self.undeclared_identifiers.add(node.name)
            def visitImport(s, node, *args):
                for (mod, alias) in node.names:
                    if alias is not None:
                        self.declared_identifiers.add(alias)
                    else:
                        self.declared_identifiers.add(mod)
            def visitFrom(s, node, *args):
                for (mod, alias) in node.names:
                    if alias is not None:
                        self.declared_identifiers.add(alias)
                    else:
                        if mod == '*':
                            raise exceptions.CompileException("'import *' is not supported, since all identifier names must be explicitly declared.  Please use the form 'from <modulename> import <name1>, <name2>, ...' instead.", lineno, pos)
                        self.declared_identifiers.add(mod)
        f = FindIdentifiers()
        visitor.walk(expr, f) #, walker=walker())

class PythonFragment(PythonCode):
    """extends PythonCode to provide identifier lookups in partial control statements
    
    e.g. 
        for x in 5:
        elif y==9:
        except (MyException, e):
    etc.
    """
    def __init__(self, code, lineno, pos):
        m = re.match(r'^(\w+)(?:\s+(.*?))?:$', code)
        if not m:
            raise exceptions.CompileException("Fragment '%s' is not a partial control statement" % code, lineno, pos)
        (keyword, expr) = m.group(1,2)
        if keyword in ['for','if', 'while']:
            code = code + "pass"
        elif keyword == 'try':
            code = code + "pass\nexcept:pass"
        elif keyword == 'elif' or keyword == 'else':
            code = "if False:pass\n" + code + "pass"
        elif keyword == 'except':
            code = "try:pass\n" + code + "pass"
        else:
            raise exceptions.CompileException("Unsupported control keyword: '%s'" % keyword, lineno, pos)
        super(PythonFragment, self).__init__(code, lineno, pos)
        
class walker(visitor.ASTVisitor):
    def dispatch(self, node, *args):
        print "Node:", str(node)
        #print "dir:", dir(node)
        return visitor.ASTVisitor.dispatch(self, node, *args)
        
class FunctionDecl(object):
    """function declaration"""
    def __init__(self, code, lineno, pos):
        self.code = code
        
        expr = parse(code, "exec")
        class ParseFunc(object):
            def visitFunction(s, node, *args):
                self.funcname = node.name
                self.argnames = node.argnames
                self.defaults = node.defaults
                self.varargs = node.varargs
                self.kwargs = node.kwargs
                
        f = ParseFunc()
        visitor.walk(expr, f)
        if not hasattr(self, 'funcname'):
            raise exceptions.CompileException("Code '%s' is not a function declaration" % code, lineno, pos)
    def get_argument_expressions(self, include_defaults=True):
        """return the argument declarations of this FunctionDecl as a printable list"""
        namedecls = []
        defaults = [d for d in self.defaults]
        kwargs = self.kwargs
        varargs = self.varargs
        argnames = [f for f in self.argnames]
        argnames.reverse()
        for arg in argnames:
            default = None
            if kwargs:
                arg = "**" + arg
                kwargs = False
            elif varargs:
                arg = "*" + arg
                varargs = False
            else:
                default = len(defaults) and defaults.pop() or None
            if include_defaults and default:
                namedecls.insert(0, "%s=%s" % (arg, ExpressionGenerator(default).value()))
            else:
                namedecls.insert(0, arg)
        return namedecls
        
class ExpressionGenerator(object):
    """given an AST node, generates an equivalent literal Python expression."""
    def __init__(self, astnode):
        self.buf = StringIO()
        visitor.walk(astnode, self) #, walker=walker())
    def value(self):
        return self.buf.getvalue()        
    def operator(self, op, node, *args):
        self.buf.write("(")
        self.visit(node.left, *args)
        self.buf.write(" %s " % op)
        self.visit(node.right, *args)
        self.buf.write(")")
    def visitConst(self, node, *args):
        self.buf.write(repr(node.value))
    def visitName(self, node, *args):
        self.buf.write(node.name)
    def visitMul(self, node, *args):
        self.operator("*", node, *args)
    def visitAdd(self, node, *args):
        self.operator("+", node, *args)
    def visitGetattr(self, node, *args):
        self.visit(node.expr, *args)
        self.buf.write(".%s" % node.attrname)
    def visitSub(self, node, *args):
        self.operator("-", node, *args)
    def visitDiv(self, node, *args):
        self.operator("/", node, *args)
    def visitSubscript(self, node, *args):
        self.visit(node.expr)
        self.buf.write("[")
        [self.visit(x) for x in node.subs]
        self.buf.write("]")
    def visitSlice(self, node, *args):
        self.visit(node.expr)
        self.buf.write("[")
        if node.lower is not None:
            self.visit(node.lower)
        self.buf.write(":")
        if node.upper is not None:
            self.visit(node.upper)
        self.buf.write("]")
    def visitCallFunc(self, node, *args):
        self.visit(node.node)
        self.buf.write("(")
        self.visit(node.args[0])
        for a in node.args[1:]:
            self.buf.write(", ")
            self.visit(a)
        self.buf.write(")")
        
        