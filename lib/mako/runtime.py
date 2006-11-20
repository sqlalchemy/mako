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
    def update(self, **args):
        """produce a copy of this Context, updating the argument dictionary
        with the given keyword arguments."""
        x = self.data.copy()
        x.update(args)
        c = Context(self.buffer, **x)
        c.with_template = self.with_template
        return c
        
class Namespace(object):
    """provides access to collections of rendering methods, which can be local, from other templates, or from imported modules"""
    def __init__(self, name, module=None, template=None, callables=None):
        self.module = module
        self.template = template
        if callables is not None:
            self.callables = dict((c.func_name, c) for c in callables)
        else:
            self.callables = {}
        
    def contextual_callable(self, context, key):
        if self.callables is not None:
            try:
                return self.callables[key]
            except KeyError:
                pass
        if self.template is not None:
            try:
                callable_ = self.template.get_component(key)
                return lambda *args, **kwargs:callable_(context, *args, **kwargs)
            except AttributeError:
                pass
        if self.module is not None:
            try:
                callable_ = getattr(self.module, key)
                return lambda *args, **kwargs:callable_(context, *args, **kwargs)
            except AttributeError:
                pass
        raise exceptions.RuntimeException("Namespace '%s' has no member '%s'" % (self.name, key))
        
        