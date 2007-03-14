# ast.py
# Copyright (C) 2006, 2007 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

"""utilities for analyzing expressions and blocks of Python code, as well as generating Python from AST nodes"""

from compiler import ast, visitor
from compiler import parse as compiler_parse
from mako import util, exceptions
from StringIO import StringIO
import re

def parse(code, mode, lineno, pos, filename):
    try:
        return compiler_parse(code, mode)
    except SyntaxError, e:
        raise exceptions.SyntaxException("(%s) %s (%s)" % (e.__class__.__name__, str(e), repr(code[0:50])), lineno, pos, filename)
    
class PythonCode(object):
    """represents information about a string containing Python code"""
    def __init__(self, code, lineno, pos, filename):
        self.code = code
        
        # represents all identifiers which are assigned to at some point in the code
        self.declared_identifiers = util.Set()
        
        # represents all identifiers which are referenced before their assignment, if any
        self.undeclared_identifiers = util.Set()
        
        # note that an identifier can be in both the undeclared and declared lists.

        # using AST to parse instead of using code.co_varnames, code.co_names has several advantages:
        # - we can locate an identifier as "undeclared" even if its declared later in the same block of code
        # - AST is less likely to break with version changes (for example, the behavior of co_names changed a little bit
        # in python version 2.5)
        if isinstance(code, basestring):
            expr = parse(code.lstrip(), "exec", lineno, pos, filename)
        else:
            expr = code
        
        class FindIdentifiers(object):
            def __init__(self):
                self.in_function = False
                self.local_ident_stack = {}
            def _add_declared(s, name):
                if not s.in_function:
                    self.declared_identifiers.add(name)
            def visitAssName(self, node, *args):
                self._add_declared(node.name)
            def visitAssign(self, node, *args):
                # flip around the visiting of Assign so the expression gets evaluated first, 
                # in the case of a clause like "x=x+5" (x is undeclared)
                self.visit(node.expr, *args)
                for n in node.nodes:
                    self.visit(n, *args)
            def visitFunction(self,node, *args):
                self._add_declared(node.name)
                # push function state onto stack.  dont log any
                # more identifiers as "declared" until outside of the function,
                # but keep logging identifiers as "undeclared".
                # track argument names in each function header so they arent counted as "undeclared"
                saved = {}
                inf = self.in_function
                self.in_function = True
                for arg in node.argnames:
                    if arg in self.local_ident_stack:
                        saved[arg] = True
                    else:
                        self.local_ident_stack[arg] = True
                for n in node.getChildNodes():
                    self.visit(n, *args)
                self.in_function = inf
                for arg in node.argnames:
                    if arg not in saved:
                        del self.local_ident_stack[arg]
            def visitFor(self, node, *args):
                # flip around visit
                self.visit(node.list, *args)
                self.visit(node.assign, *args)
                self.visit(node.body, *args)
            def visitName(s, node, *args):
                if node.name not in __builtins__ and node.name not in self.declared_identifiers and node.name not in s.local_ident_stack:
                    self.undeclared_identifiers.add(node.name)
            def visitImport(self, node, *args):
                for (mod, alias) in node.names:
                    if alias is not None:
                        self._add_declared(alias)
                    else:
                        self._add_declared(mod.split('.')[0])
            def visitFrom(self, node, *args):
                for (mod, alias) in node.names:
                    if alias is not None:
                        self._add_declared(alias)
                    else:
                        if mod == '*':
                            raise exceptions.CompileException("'import *' is not supported, since all identifier names must be explicitly declared.  Please use the form 'from <modulename> import <name1>, <name2>, ...' instead.", lineno, pos, filename)
                        self._add_declared(mod)
        f = FindIdentifiers()
        visitor.walk(expr, f) #, walker=walker())

class ArgumentList(object):
    """parses a fragment of code as a comma-separated list of expressions"""
    def __init__(self, code, lineno, pos, filename):
        self.codeargs = []
        self.args = []
        self.declared_identifiers = util.Set()
        self.undeclared_identifiers = util.Set()
        class FindTuple(object):
            def visitTuple(s, node, *args):
                for n in node.nodes:
                    p = PythonCode(n, lineno, pos, filename)
                    self.codeargs.append(p)
                    self.args.append(ExpressionGenerator(n).value())
                    self.declared_identifiers = self.declared_identifiers.union(p.declared_identifiers)
                    self.undeclared_identifiers = self.undeclared_identifiers.union(p.undeclared_identifiers)
        if isinstance(code, basestring):
            if re.match(r"\S", code) and not re.match(r",\s*$", code):
                # if theres text and no trailing comma, insure its parsed
                # as a tuple by adding a trailing comma
                code  += ","
            expr = parse(code, "exec", lineno, pos, filename)
        else:
            expr = code

        f = FindTuple()
        visitor.walk(expr, f)
        
class PythonFragment(PythonCode):
    """extends PythonCode to provide identifier lookups in partial control statements
    
    e.g. 
        for x in 5:
        elif y==9:
        except (MyException, e):
    etc.
    """
    def __init__(self, code, lineno, pos, filename):
        m = re.match(r'^(\w+)(?:\s+(.*?))?:$', code.strip())
        if not m:
            raise exceptions.CompileException("Fragment '%s' is not a partial control statement" % code, lineno, pos, filename)
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
            raise exceptions.CompileException("Unsupported control keyword: '%s'" % keyword, lineno, pos, filename)
        super(PythonFragment, self).__init__(code, lineno, pos, filename)
        
class walker(visitor.ASTVisitor):
    def dispatch(self, node, *args):
        print "Node:", str(node)
        #print "dir:", dir(node)
        return visitor.ASTVisitor.dispatch(self, node, *args)
        
class FunctionDecl(object):
    """function declaration"""
    def __init__(self, code, lineno, pos, filename, allow_kwargs=True):
        self.code = code
        expr = parse(code, "exec", lineno, pos, filename)
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
            raise exceptions.CompileException("Code '%s' is not a function declaration" % code, lineno, pos, filename)
        if not allow_kwargs and self.kwargs:
            raise exceptions.CompileException("'**%s' keyword argument not allowed here" % self.argnames[-1], lineno, pos, filename)
            
    def get_argument_expressions(self, include_defaults=True):
        """return the argument declarations of this FunctionDecl as a printable list."""
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

class FunctionArgs(FunctionDecl):
    """the argument portion of a function declaration"""
    def __init__(self, code, lineno, pos, filename, **kwargs):
        super(FunctionArgs, self).__init__("def ANON(%s):pass" % code, lineno, pos, filename, **kwargs)
        
            
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
    def booleanop(self, op, node, *args):
        self.visit(node.nodes[0])
        for n in node.nodes[1:]:
            self.buf.write(" " + op + " ")
            self.visit(n, *args)
    def visitConst(self, node, *args):
        self.buf.write(repr(node.value))
    def visitAssName(self, node, *args):
        # TODO: figure out OP_ASSIGN, other OP_s
        self.buf.write(node.name)
    def visitName(self, node, *args):
        self.buf.write(node.name)
    def visitMul(self, node, *args):
        self.operator("*", node, *args)
    def visitAnd(self, node, *args):
        self.booleanop("and", node, *args)
    def visitOr(self, node, *args):
        self.booleanop("or", node, *args)
    def visitBitand(self, node, *args):
        self.booleanop("&", node, *args)
    def visitBitor(self, node, *args):
        self.booleanop("|", node, *args)
    def visitBitxor(self, node, *args):
        self.booleanop("^", node, *args)
    def visitAdd(self, node, *args):
        self.operator("+", node, *args)
    def visitGetattr(self, node, *args):
        self.visit(node.expr, *args)
        self.buf.write(".%s" % node.attrname)
    def visitSub(self, node, *args):
        self.operator("-", node, *args)
    def visitNot(self, node, *args):
        self.buf.write("not ")
        self.visit(node.expr)
    def visitDiv(self, node, *args):
        self.operator("/", node, *args)
    def visitFloorDiv(self, node, *args):
        self.operator("//", node, *args)
    def visitSubscript(self, node, *args):
        self.visit(node.expr)
        self.buf.write("[")
        [self.visit(x) for x in node.subs]
        self.buf.write("]")
    def visitUnarySub(self, node, *args):
        self.buf.write("-")
        self.visit(node.expr)
    def visitUnaryAdd(self, node, *args):
        self.buf.write("-")
        self.visit(node.expr)
    def visitSlice(self, node, *args):
        self.visit(node.expr)
        self.buf.write("[")
        if node.lower is not None:
            self.visit(node.lower)
        self.buf.write(":")
        if node.upper is not None:
            self.visit(node.upper)
        self.buf.write("]")
    def visitDict(self, node):
        self.buf.write("{")
        c = node.getChildren()
        for i in range(0, len(c), 2):
            self.visit(c[i])
            self.buf.write(": ")
            self.visit(c[i+1])
            if i<len(c) -2:
                self.buf.write(", ")
        self.buf.write("}")
    def visitTuple(self, node):
        self.buf.write("(")
        c = node.getChildren()
        for i in range(0, len(c)):
            self.visit(c[i])
            if i<len(c) - 1:
                self.buf.write(", ")
        self.buf.write(")")
    def visitList(self, node):
        self.buf.write("[")
        c = node.getChildren()
        for i in range(0, len(c)):
            self.visit(c[i])
            if i<len(c) - 1:
                self.buf.write(", ")
        self.buf.write("]")
    def visitListComp(self, node):
        self.buf.write("[")
        self.visit(node.expr)
        self.buf.write(" ")
        for n in node.quals:
            self.visit(n)
        self.buf.write("]")
    def visitListCompFor(self, node):
        self.buf.write(" for ")
        self.visit(node.assign)
        self.buf.write(" in ")
        self.visit(node.list)
        for n in node.ifs:
            self.visit(n)
    def visitListCompIf(self, node):
        self.buf.write(" if ")
        self.visit(node.test)
    def visitCompare(self, node):
        self.visit(node.expr)
        for tup in node.ops:
            self.buf.write(tup[0])
            self.visit(tup[1])
    def visitCallFunc(self, node, *args):
        self.visit(node.node)
        self.buf.write("(")
        if len(node.args):
            self.visit(node.args[0])
            for a in node.args[1:]:
                self.buf.write(", ")
                self.visit(a)
        self.buf.write(")")
        
        