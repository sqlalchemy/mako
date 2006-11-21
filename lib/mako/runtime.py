# runtime.py
# Copyright (C) 2006 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

"""provides the Context class, the runtime namespace for templates."""
from mako import exceptions

class Context(object):
    """provides runtime namespace and output buffer for templates."""
    def __init__(self, template, buffer, **data):
        # TODO: not sure if Context should need template + buffer etc.
        self.buffer = buffer
        self.stack = [data]
        # the Template instance currently rendering with this context.
        self.with_template = template
    def __getitem__(self, key):
        return self.stack[-1][key]
    def get(self, key, default=None):
        return self.stack[-1].get(key, default)
    def write(self, string):
        self.buffer.write(string)
    def update(self, **args):
        """produce a copy of this Context, updating the argument dictionary
        with the given keyword arguments."""
        self.stack[-1].update(args)
    def push(self, **args):
        x = self.stack[-1].copy()
        x.update(args)
        self.stack.append(x)
    def pop(self):
        self.stack.pop()
        
class Namespace(object):
    """provides access to collections of rendering methods, which can be local, from other templates, or from imported modules"""
    def __init__(self, name, module=None, template=None, callables=None):
        self.module = module
        self.template = template
        if callables is not None:
            self.callables = dict([(c.func_name, c) for c in callables])
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
        
def include_file(context, uri, import_symbols):
    lookup = context.with_template.lookup
    template = lookup.get_template(uri)
    template.render_context(context)
        
