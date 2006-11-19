"""provides the Template class, a facade for parsing, generating and executing template strings."""

from mako.lexer import Lexer
from mako.codegen import Compiler
from mako.context import Context
import imp, time, inspect, weakref, sys
from StringIO import StringIO

_modules = weakref.WeakValueDictionary()
_inmemory_templates = weakref.WeakValueDictionary()

class _ModuleMarker(object):
    """enables weak-referencing to module instances"""
    def __init__(self, module):
        self.module = module

class Template(object):
    """a compiled template"""
    def __init__(self, text=None, module=None, identifier=None, filename=None, format_exceptions=True, error_handler=None):
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
            module = _compile_text(text, self.identifier, filename)
            _inmemory_templates[module.__name__] = self
            self._source = text
        else:
            self._source = None
        self.module = module
        self.format_exceptions = format_exceptions
        self.error_handler = error_handler
        _modules[module.__name__] = _ModuleMarker(module)

    def get_source(self):
        if self._source is not None:
            return self._source
        else:
            filename = self.module._template_filename
            if not filename:
                raise exceptions.RuntimeException("Cant get source code or template filename for template: %s" % self.identifier)
            return file(filename).read()
            
    def render(self, *args, **data):
        """render the output of this template as a string.
        
        a Context object is created corresponding to the given data.  Arguments that are explictly
        declared by this template's internal rendering method are also pulled from the given *args, **data 
        members."""
        return _render(self, self.module.render, *args, **data)
    
    def render_context(self, context, *args, **kwargs):
        """render this Template with the given context.  
        
        the data is written to the context's buffer."""
        _render_context(self, self.module.render, context, *args, **kwargs)
        
    def get_component(self, name):
        """return a component of this template as an individual Template of its own."""
        return ComponentTemplate(self, getattr(self.module, "render_%s" % name))
        
class ComponentTemplate(Template):
    """a Template which represents a callable component in a parent template."""
    def __init__(self, parent, callable_):
        self.parent = parent
        self.callable_ = callable_
    def render(self, *args, **data):
        """render the output of this template as a string.
        
        a Context object is created corresponding to the given data.  Arguments that are explictly
        declared by this template's internal rendering method are also pulled from the given *args, **data 
        members."""
        return _render(self.parent, self.callable_, *args, **data)

    def render_context(self, context, *args, **kwargs):
        """render this Template with the given context.  
        
        the data is written to the context's buffer."""
        _render_context(self.parent, self.callable_, context, *args, **kwargs)

def _compile_text(text, identifier, filename):
    node = Lexer(text).parse()
    source = Compiler(node).render()
#    print source
    cid = identifier
    module = imp.new_module(cid)
    code = compile(source, filename or cid, 'exec')
    exec code in module.__dict__, module.__dict__
    module._modified_time = time.time()
    return module
    
def _render(template, callable_, *args, **data):
    """given a Template and a callable_ from that template, create a Context and return the string output."""
    buf = StringIO()
    context = Context(buf, **data)
    kwargs = {}
    argspec = inspect.getargspec(callable_)
    namedargs = argspec[0] + [v for v in argspec[1:3] if v is not None]
    for arg in namedargs:
        if arg != 'context' and arg in data:
            kwargs[arg] = data[arg]
    _render_context(template, callable_, context, *args, **kwargs)
    return buf.getvalue()

def _render_context(template, callable_, context, *args, **kwargs):
    context.with_template = template
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
            source = _get_template_source(callable_)
            raise error
    else:
        callable_(context, *args, **kwargs)
    
def _get_template_source(callable_):
    """return the source code for the template that produced the given rendering callable"""
    name = callable_.func_globals['__name__']
    try:
        template = _inmemory_templates[name]
        source = template._source
    except KeyError:
        module = _modules[name].module
        filename = module._template_filename
        if filename is None:
            if not filename:
                raise exceptions.RuntimeException("Cant get source code or template filename for template: %s" % self.identifier)
        return file(filename).read()
            
