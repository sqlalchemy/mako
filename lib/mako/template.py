# template.py
# Copyright (C) 2006 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

"""provides the Template class, a facade for parsing, generating and executing template strings,
as well as template runtime operations."""

from mako.lexer import Lexer
from mako.codegen import Compiler
from mako.runtime import Context
from mako import util
import imp, time, inspect, weakref, sys

_modules = weakref.WeakValueDictionary()
_inmemory_templates = weakref.WeakValueDictionary()

class _ModuleMarker(object):
    """enables weak-referencing to module instances"""
    def __init__(self, module):
        self.module = module

class Template(object):
    """a compiled template"""
    def __init__(self, text=None, module=None, identifier=None, filename=None, format_exceptions=True, error_handler=None, lookup=None):
        """construct a new Template instance using either literal template text, or a previously loaded template module
        
        text - textual template source, or None if a module is to be provided
        
        module - a Python module, such as loaded via __import__ or similar.  the module should contain at least one
        function render(context) that renders with the given context.  
        
        identifier - the "id" of this template.  defaults to the identifier of the given module, or for text
        the hex string of this Template's object id
        
        filename - filename of the source template, compiled into the module.
        
        format_exceptions - if caught exceptions should be formatted as template output, including a stack
        trace adjusted to the source template
        """
        self.identifier = identifier or "memory:" + hex(id(self))
        if text is not None:
            (code, module) = _compile_text(text, self.identifier, filename)
            _inmemory_templates[module.__name__] = self
            self._code = code
            self._source = text
        else:
            self._source = None
            self._code = None
        self.module = module
        self.callable_ = self.module.render
        self.format_exceptions = format_exceptions
        self.error_handler = error_handler
        self.lookup = lookup
        _modules[module.__name__] = _ModuleMarker(module)

    source = property(lambda self:_get_template_source(self.callable_), doc="""return the template source code for this Template.""")
    code = property(lambda self:_get_module_source(self.callable_), doc="""return the module source code for this Template""")
        
    def render(self, *args, **data):
        """render the output of this template as a string.
        
        a Context object is created corresponding to the given data.  Arguments that are explictly
        declared by this template's internal rendering method are also pulled from the given *args, **data 
        members."""
        return _render(self, self.callable_, *args, **data)
    
    def render_context(self, context, *args, **kwargs):
        """render this Template with the given context.  
        
        the data is written to the context's buffer."""
        _render_context(self, self.callable_, context, *args, **kwargs)
        
    def get_component(self, name):
        """return a component of this template as an individual Template of its own."""
        return ComponentTemplate(self, getattr(self.module, "render_%s" % name))
        
class ComponentTemplate(Template):
    """a Template which represents a callable component in a parent template."""
    def __init__(self, parent, callable_):
        self.parent = parent
        self.callable_ = callable_
    def get_component(self, name):
        return self.parent.get_component(name)
        
def _compile_text(text, identifier, filename):
    node = Lexer(text).parse()
    source = Compiler(node).render()
    #print source
    cid = identifier
    module = imp.new_module(cid)
    code = compile(source, filename or cid, 'exec')
    exec code in module.__dict__, module.__dict__
    return (source, module)
    
def _render(template, callable_, *args, **data):
    """given a Template and a callable_ from that template, create a Context and return the string output."""
    buf = util.StringIO()
    context = Context(template, buf, **data)
    kwargs = {}
    argspec = inspect.getargspec(callable_)
    namedargs = argspec[0] + [v for v in argspec[1:3] if v is not None]
    for arg in namedargs:
        if arg != 'context' and arg in data:
            kwargs[arg] = data[arg]
    _render_context(template, callable_, context, *args, **kwargs)
    return buf.getvalue()

def _render_context(template, callable_, context, *args, **kwargs):
    _exec_template(callable_, context, args=args, kwargs=kwargs)

def _exec_template(callable_, context, args=None, kwargs=None):
    """execute a rendering callable given the callable, a Context, and optional explicit arguments
    
    the contextual Template will be located if it exists, and the error handling options specified
    on that Template will be interpreted here.
    """
    template = context.with_template
    if template is not None and (template.format_exceptions or template.error_handler):
        error = None
        try:
            callable_(context, *args, **kwargs)
        except Exception, e:
            error = e
        except:                
            e = sys.exc_info()[0]
            error = e
        if error:
            if template.error_handler:
                result = template.error_handler(context, error)
                if not result:
                    raise error
            else:
                # TODO
                source = _get_template_source(callable_)
                raise error
    else:
        callable_(context, *args, **kwargs)
    
def _get_template_source(callable_):
    """return the source code for the template that produced the given rendering callable"""
    name = callable_.func_globals['__name__']
    try:
        template = _inmemory_templates[name]
        return template._source
    except KeyError:
        module = _modules[name].module
        filename = module._template_filename
        if filename is None:
            if not filename:
                raise exceptions.RuntimeException("Cant get source code or template filename for template: %s" % name)
        return file(filename).read()

def _get_module_source(callable_):
    name = callable_.func_globals['__name__']
    try:
        template = _inmemory_templates[name]
        return template._code
    except KeyError:
        module = _modules[name].module
        filename = module.__file__
        if filename is None:
            if not filename:
                raise exceptions.RuntimeException("Cant get module source code or module filename for template: %s" % name)
        return file(filename).read()
                
