# ast.py

from compiler import ast, parse, visitor
from mako import util

class PythonCode(object):
    """represents information about a string containing Python code"""
    def __init__(self, code):
        self.code = code
        self.declared_identifiers = util.Set()
        self.undeclared_identifiers = util.Set()
        
        expr = parse(code, "exec")
        class FindIdentifiers(object):
            def visitAssName(s, node, *args, **kwargs):
                if node.name not in self.undeclared_identifiers:
                    self.declared_identifiers.add(node.name)
            def visitName(s, node, *args, **kwargs):
                if node.name not in __builtins__ and node.name not in self.declared_identifiers:
                    self.undeclared_identifiers.add(node.name)
        f = FindIdentifiers()
        visitor.walk(expr, f)

