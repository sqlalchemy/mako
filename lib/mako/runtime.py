"""provides the Context class, the runtime namespace for templates."""
from mako import exceptions

class Context(object):
    """provides runtime namespace and output buffer for templates."""
    def __init__(self, buffer, **data):
        self.buffer = buffer
        self.data = data
        # the Template instance currently rendering with this context.
        self.with_template = None
    def __getitem__(self, key):
        return self.data[key]
    def get(self, key, default=None):
        return self.data.get(key, default)
    def write(self, string):
        self.buffer.write(string)
        
        
class Namespace(object):
    """provides access to collections of rendering methods, which can be local, from other templates, or from imported modules"""
    def __init__(self, name, module=None, template=None, callables=None):
        self.module = module
        self.template = template
        self.callables = callables
        
    def load(self, key):
        if self.callables is not None:
            try:
                return self.callables[key]
            except KeyError:
                pass
        if self.template is not None:
            try:
                return self.template.get_component(key)
            except AttributeError:
                pass
        if self.module is not None:
            try:
                return getattr(self.module, key)
            except AttributeError:
                pass
        raise exceptions.RuntimeException("Namespace '%s' has no member '%s'" % (self.name, key))
        
    def contextual_callable(self, context, key):
        return lambda context, *args, **kwargs:self.load(key)(context, *args, **kwargs)
        