"""object model defining a Mako template."""

from mako import exceptions

class Node(object):
    """base class for a Node in the parse tree."""
    def __init__(self, lineno, pos):
        self.lineno = lineno
        self.pos = pos

class ControlLine(Node):
    """defines a control line, a line-oriented python line or end tag.
    
    % if foo:
        (markup)
    % endif
    """
    def __init__(self, keyword, isend, text, **kwargs):
        super(ControlLine, self).__init__(**kwargs)
        self.keyword = keyword
        self.text = text
        self.isend = isend
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
    def __repr__(self):
        return "Comment(%s, %s, %s)" % (repr(self.text), repr(self.ismodule), repr((self.lineno, self.pos)))
        
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
    def __init__(self, text, **kwargs):
        super(Expression, self).__init__(**kwargs)
        self.text = text
    def __repr__(self):
        return "Expression(%s, %s)" % (self.text, repr((self.lineno, self.pos)))
        
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
            raise exceptions.CompileError("No such tag: '%s'" % keyword)
        return type.__call__(cls, keyword, attributes, **kwargs)
        
class Tag(Node):
    """base class for tags.
    
    <%sometag/>
    
    <%someothertag>
        stuff
    </%someothertag>
    """
    __metaclass__ = _TagMeta
    __keyword__ = None
    def __init__(self, keyword, attributes, **kwargs):
        super(Tag, self).__init__(**kwargs)
        self.keyword = keyword
        self.attributes = attributes
        self.nodes = []
    def __repr__(self):
        return "%s(%s, %s, %s, %s)" % (self.__class__.__name__, repr(self.keyword), repr(self.attributes), repr((self.lineno, self.pos)), repr([repr(x) for x in self.nodes]))
        
class IncludeTag(Tag):
    __keyword__ = 'include'
class NamespaceTag(Tag):
    __keyword__ = 'namespace'
class ComponentTag(Tag):
    __keyword__ = 'component'
class CallTag(Tag):
    __keyword__ = 'call'
