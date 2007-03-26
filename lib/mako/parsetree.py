# parsetree.py
# Copyright (C) 2006, 2007 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

"""defines the parse tree components for Mako templates."""

from mako import exceptions, ast, util, filters
import re

class Node(object):
    """base class for a Node in the parse tree."""
    def __init__(self, lineno, pos, filename):
        self.lineno = lineno
        self.pos = pos
        self.filename = filename
    def get_children(self):
        return []
    def accept_visitor(self, visitor):
        def traverse(node):
            for n in node.get_children():
                n.accept_visitor(visitor)
        method = getattr(visitor, "visit" + self.__class__.__name__, traverse)
        method(self)

class TemplateNode(Node):
    """a 'container' node that stores the overall collection of nodes."""
    def __init__(self, filename):
        super(TemplateNode, self).__init__(0, 0, filename)
        self.nodes = []
        self.page_attributes = {}
    def get_children(self):
        return self.nodes
    def __repr__(self):
        return "TemplateNode(%s, %s)" % (repr(self.page_attributes), repr(self.nodes))
        
class ControlLine(Node):
    """defines a control line, a line-oriented python line or end tag.
    
    % if foo:
        (markup)
    % endif
    """
    def __init__(self, keyword, isend, text, **kwargs):
        super(ControlLine, self).__init__(**kwargs)
        self.text = text
        self.keyword = keyword
        self.isend = isend
        self.is_primary = keyword in ['for','if', 'while', 'try']
        if self.isend:
            self._declared_identifiers = []
            self._undeclared_identifiers = []
        else:
            code = ast.PythonFragment(text, self.lineno, self.pos, self.filename)
            (self._declared_identifiers, self._undeclared_identifiers) = (code.declared_identifiers, code.undeclared_identifiers)
    def declared_identifiers(self):
        return self._declared_identifiers
    def undeclared_identifiers(self):
        return self._undeclared_identifiers
    def is_ternary(self, keyword):
        """return true if the given keyword is a ternary keyword for this ControlLine"""
        return keyword in {
            'if':util.Set(['else', 'elif']),
            'try':util.Set(['except', 'finally']),
            'for':util.Set(['else'])
        }.get(self.keyword, [])
    def __repr__(self):
        return "ControlLine(%s, %s, %s, %s)" % (repr(self.keyword), repr(self.text), repr(self.isend), repr((self.lineno, self.pos)))

class Text(Node):
    """defines plain text in the template."""
    def __init__(self, content, **kwargs):
        super(Text, self).__init__(**kwargs)
        self.content = content
    def __repr__(self):
        return "Text(%s, %s)" % (repr(self.content), repr((self.lineno, self.pos)))
        
class Code(Node):
    """defines a Python code block, either inline or module level.
    
    inline:
    <%
        x = 12
    %>
    
    module level:
    <%!
        import logger
    %>
    
    """
    def __init__(self, text, ismodule, **kwargs):
        super(Code, self).__init__(**kwargs)
        self.text = text
        self.ismodule = ismodule
        self.code = ast.PythonCode(text, self.lineno, self.pos, self.filename)
    def declared_identifiers(self):
        return self.code.declared_identifiers
    def undeclared_identifiers(self):
        return self.code.undeclared_identifiers
    def __repr__(self):
        return "Code(%s, %s, %s)" % (repr(self.text), repr(self.ismodule), repr((self.lineno, self.pos)))
        
class Comment(Node):
    """defines a comment line.
    
    # this is a comment
    
    """
    def __init__(self, text, **kwargs):
        super(Comment, self).__init__(**kwargs)
        self.text = text
    def __repr__(self):
        return "Comment(%s, %s)" % (repr(self.text), repr((self.lineno, self.pos)))
        
class Expression(Node):
    """defines an inline expression.
    
    ${x+y}
    
    """
    def __init__(self, text, escapes, **kwargs):
        super(Expression, self).__init__(**kwargs)
        self.text = text
        self.escapes = escapes
        self.escapes_code = ast.ArgumentList(escapes, self.lineno, self.pos, self.filename)
        self.code = ast.PythonCode(text, self.lineno, self.pos, self.filename)
    def declared_identifiers(self):
        return []
    def undeclared_identifiers(self):
        # TODO: make the "filter" shortcut list configurable at parse/gen time
        return self.code.undeclared_identifiers.union(self.escapes_code.undeclared_identifiers.difference(util.Set(filters.DEFAULT_ESCAPES.keys())))
    def __repr__(self):
        return "Expression(%s, %s, %s)" % (repr(self.text), repr(self.escapes_code.args), repr((self.lineno, self.pos)))
        
class _TagMeta(type):
    """metaclass to allow Tag to produce a subclass according to its keyword"""
    _classmap = {}
    def __init__(cls, clsname, bases, dict):
        if cls.__keyword__ is not None:
            cls._classmap[cls.__keyword__] = cls
            super(_TagMeta, cls).__init__(clsname, bases, dict)
    def __call__(cls, keyword, attributes, **kwargs):
        try:
            cls = _TagMeta._classmap[keyword]
        except KeyError:
            raise exceptions.CompileException("No such tag: '%s'" % keyword, kwargs['lineno'], kwargs['pos'], kwargs['filename'])
        return type.__call__(cls, keyword, attributes, **kwargs)
        
class Tag(Node):
    """abstract base class for tags.
    
    <%sometag/>
    
    <%someothertag>
        stuff
    </%someothertag>
    """
    __metaclass__ = _TagMeta
    __keyword__ = None
    def __init__(self, keyword, attributes, expressions, nonexpressions, required, **kwargs):
        """construct a new Tag instance.
        
        this constructor not called directly, and is only called by subclasses.
        
        keyword - the tag keyword
        
        attributes - raw dictionary of attribute key/value pairs
        
        expressions - a util.Set of identifiers that are legal attributes, which can also contain embedded expressions
        
        nonexpressions - a util.Set of identifiers that are legal attributes, which cannot contain embedded expressions
        
        **kwargs - other arguments passed to the Node superclass (lineno, pos)"""
        super(Tag, self).__init__(**kwargs)
        self.keyword = keyword
        self.attributes = attributes
        self._parse_attributes(expressions, nonexpressions)
        missing = [r for r in required if r not in self.parsed_attributes]
        if len(missing):
            raise exceptions.CompileException("Missing attribute(s): %s" % ",".join([repr(m) for m in missing]), self.lineno, self.pos, self.filename)
        self.parent = None
        self.nodes = []
    def is_root(self):
        return self.parent is None
    def get_children(self):
        return self.nodes
    def _parse_attributes(self, expressions, nonexpressions):
        undeclared_identifiers = util.Set()
        self.parsed_attributes = {}
        for key in self.attributes:
            if key in expressions:
                expr = []
                for x in re.split(r'(\${.+?})', self.attributes[key]):
                    m = re.match(r'^\${(.+?)}$', x)
                    if m:
                        code = ast.PythonCode(m.group(1), self.lineno, self.pos, self.filename)
                        undeclared_identifiers = undeclared_identifiers.union(code.undeclared_identifiers)
                        expr.append(m.group(1))
                    else:
                        if x:
                            expr.append(repr(x))
                self.parsed_attributes[key] = " + ".join(expr)
            elif key in nonexpressions:
                if re.search(r'${.+?}', self.attributes[key]):
                    raise exceptions.CompileException("Attibute '%s' in tag '%s' does not allow embedded expressions"  %(key, self.keyword), self.lineno, self.pos, self.filename)
                self.parsed_attributes[key] = repr(self.attributes[key])
            else:
                raise exceptions.CompileException("Invalid attribute for tag '%s': '%s'" %(self.keyword, key), self.lineno, self.pos, self.filename)
        self.expression_undeclared_identifiers = undeclared_identifiers
    def declared_identifiers(self):
        return []
    def undeclared_identifiers(self):
        return self.expression_undeclared_identifiers
    def __repr__(self):
        return "%s(%s, %s, %s, %s)" % (self.__class__.__name__, repr(self.keyword), repr(self.attributes), repr((self.lineno, self.pos)), repr([repr(x) for x in self.nodes]))
        
class IncludeTag(Tag):
    __keyword__ = 'include'
    def __init__(self, keyword, attributes, **kwargs):
        super(IncludeTag, self).__init__(keyword, attributes, ('file', 'import', 'args'), (), ('file',), **kwargs)
        self.page_args = ast.PythonCode("foo(%s)" % attributes.get('args', ''), self.lineno, self.pos, self.filename)
    def declared_identifiers(self):
        return []
    def undeclared_identifiers(self):
        identifiers = self.page_args.undeclared_identifiers
        return identifiers.union(super(IncludeTag, self).undeclared_identifiers())
    
class NamespaceTag(Tag):
    __keyword__ = 'namespace'
    def __init__(self, keyword, attributes, **kwargs):
        super(NamespaceTag, self).__init__(keyword, attributes, (), ('name','inheritable','file','import','module'), (), **kwargs)
        self.name = attributes.get('name', '__anon_%s' % hex(abs(id(self))))
        if not 'name' in attributes and not 'import' in attributes:
            raise exceptions.CompileException("'name' and/or 'import' attributes are required for <%namespace>", self.lineno, self.pos, self.filename)
    def declared_identifiers(self):
        return []

class TextTag(Tag):
    __keyword__ = 'text'
    def __init__(self, keyword, attributes, **kwargs):
        super(TextTag, self).__init__(keyword, attributes, (), ('filter'), (), **kwargs)
        self.filter_args = ast.ArgumentList(attributes.get('filter', ''), self.lineno, self.pos, self.filename)
        
class DefTag(Tag):
    __keyword__ = 'def'
    def __init__(self, keyword, attributes, **kwargs):
        super(DefTag, self).__init__(keyword, attributes, ('buffered', 'cached', 'cache_key', 'cache_timeout', 'cache_type', 'cache_dir', 'cache_url'), ('name','filter'), ('name',), **kwargs)
        name = attributes['name']
        if re.match(r'^[\w_]+$',name):
            raise exceptions.CompileException("Missing parenthesis in %def", self.lineno, self.pos, self.filename)
        self.function_decl = ast.FunctionDecl("def " + name + ":pass", self.lineno, self.pos, self.filename)
        self.name = self.function_decl.funcname
        self.filter_args = ast.ArgumentList(attributes.get('filter', ''), self.lineno, self.pos, self.filename)
    def declared_identifiers(self):
        return self.function_decl.argnames
    def undeclared_identifiers(self):
        res = []
        for c in self.function_decl.defaults:
            res += list(ast.PythonCode(c, self.lineno, self.pos, self.filename).undeclared_identifiers)
        return res + list(self.filter_args.undeclared_identifiers.difference(util.Set(filters.DEFAULT_ESCAPES.keys())))

class CallTag(Tag):
    __keyword__ = 'call'
    def __init__(self, keyword, attributes, **kwargs):
        super(CallTag, self).__init__(keyword, attributes, ('args'), ('expr',), ('expr',), **kwargs)
        self.code = ast.PythonCode(attributes['expr'], self.lineno, self.pos, self.filename)
        self.body_decl = ast.FunctionArgs(attributes.get('args', ''), self.lineno, self.pos, self.filename)
    def declared_identifiers(self):
        return self.code.declared_identifiers.union(self.body_decl.argnames)
    def undeclared_identifiers(self):
        return self.code.undeclared_identifiers

class InheritTag(Tag):
    __keyword__ = 'inherit'
    def __init__(self, keyword, attributes, **kwargs):
        super(InheritTag, self).__init__(keyword, attributes, ('file',), (), ('file',), **kwargs)

class PageTag(Tag):
    __keyword__ = 'page'
    def __init__(self, keyword, attributes, **kwargs):
        super(PageTag, self).__init__(keyword, attributes, ('cached', 'cache_key', 'cache_timeout', 'cache_type', 'cache_dir', 'cache_url', 'args', 'expression_filter'), (), (), **kwargs)
        self.body_decl = ast.FunctionArgs(attributes.get('args', ''), self.lineno, self.pos, self.filename)
        self.filter_args = ast.ArgumentList(attributes.get('expression_filter', ''), self.lineno, self.pos, self.filename)
    def declared_identifiers(self):
        return self.body_decl.argnames
        
    
