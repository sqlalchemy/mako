# ast.py

from compiler import ast, parse, visitor
from mako import util
from StringIO import StringIO

class PythonCode(object):
    """represents information about a string containing Python code"""
    def __init__(self, code):
        self.code = code
        self.declared_identifiers = util.Set()
        self.undeclared_identifiers = util.Set()
        
        expr = parse(code, "exec")
        class FindIdentifiers(object):
            def visitAssName(s, node, *args):
                if node.name not in self.undeclared_identifiers:
                    self.declared_identifiers.add(node.name)
            def visitName(s, node, *args):
                if node.name not in __builtins__ and node.name not in self.declared_identifiers:
                    self.undeclared_identifiers.add(node.name)
        f = FindIdentifiers()
        visitor.walk(expr, f)

class walker(visitor.ASTVisitor):
    def dispatch(self, node, *args):
        print "Node:", str(node)
        #print "dir:", dir(node)
        return visitor.ASTVisitor.dispatch(self, node, *args)
        
class FunctionDecl(object):
    """function declaration"""
    def __init__(self, code):
        self.code = code
        
        expr = parse(code, "exec")
        class ParseFunc(object):
            def visitFunction(s, node, *args, **kwargs):
                self.funcname = node.name
                self.argnames = node.argnames
                self.defaults = node.defaults
        f = ParseFunc()
        visitor.walk(expr, f)

class ExpressionGenerator(object):
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
        print node, dir(node)
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
        
        