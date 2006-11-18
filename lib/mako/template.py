"""provides the Template class, a facade for parsing, generating and executing template strings."""

from mako.lexer import Lexer
from mako.codegen import Compiler
from mako.context import Context
import imp, time, inspect
from StringIO import StringIO

class Template(object):
    """a compiled template"""
    def __init__(self, text=None, module=None, identifier=None, filename=''):
        """construct a new Template instance using either literal template text, or a previously loaded template module
        
        text - textual template source, or None if a module is to be provided
        
        module - a Python module, such as loaded via __import__ or similar.  the module should contain at least one
        function render(context) that renders with the given context.  
        
        identifier - the "id" of this template.  defaults to the identifier of the given module, or for text
        the hex string of this Template's object id
        
        filename - filename of the source template, compiled into the module.
        
        """
        if text is not None:
            self.module = _compile_text(text, identifier or hex(id(self)), filename)
        else:
            self.module = module

    def render(self, *args, **data):
        """render the output of this template as a string.
        
        a Context object is created corresponding to the given data.  Arguments that are explictly
        declared by this template's internal rendering method are also pulled from the given *args, **data 
        members."""
        return _render(self.module.render, *args, **data)
    
    def get_component(self, name):
        """return a component of this template as an individual Template of its own."""
        return ComponentTemplate(getattr(self.module, "render_%s" % name))
        
class ComponentTemplate(Template):
    """a Template which represents a callable component in a parent template."""
    def __init__(self, callable_):
        self.callable_ = callable_
    def render(self, *args, **data):
        """render the output of this template as a string.
        
        a Context object is created corresponding to the given data.  Arguments that are explictly
        declared by this template's internal rendering method are also pulled from the given *args, **data 
        members."""
        return _render(self.callable_, *args, **data)

def _compile_text(text, identifier, filename):
    node = Lexer(text).parse()
    source = Compiler(node).render()
    print source
    cid = identifier
    module = imp.new_module(cid)
    code = compile(source, filename, 'exec')
    exec code in module.__dict__, module.__dict__
    module._modified_time = time.time()
    return module
    
def _render(callable_, *args, **data):
    buf = StringIO()
    context = Context(buf, **data)
    kwargs = {}
    argspec = inspect.getargspec(callable_)
    namedargs = argspec[0] + [v for v in argspec[1:3] if v is not None]
    for arg in namedargs:
        if arg != 'context' and arg in data:
            kwargs[arg] = data[arg]
    callable_(context, *args, **kwargs)
    return buf.getvalue()
    