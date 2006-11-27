# runtime.py
# Copyright (C) 2006 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

"""provides the Context class, the runtime namespace for templates."""
from mako import exceptions, util
import inspect
        
class Context(object):
    """provides runtime namespace, output buffer, and various callstacks for templates."""
    def __init__(self, buffer, **data):
        self._buffer_stack = [buffer]
        self._data = data
        self._with_template = None
        self.namespaces = {}
        
        # "capture" function which proxies to the generic "capture" function
        data['capture'] = lambda x, *args, **kwargs: capture(self, x, *args, **kwargs)
        
        # "caller" stack used by def calls with content
        self.caller_stack = [Undefined]
        data['caller'] = _StackFacade(self.caller_stack)

    def keys(self):
        return self._data.keys()
    def __getitem__(self, key):
        return self._data[key]
    def _put(self, key, value):
        self._data[key] = value
    def push_buffer(self):
        """push a capturing buffer onto this Context."""
        self._buffer_stack.append(util.FastEncodingBuffer())
    def pop_buffer(self):
        """pop the most recent capturing buffer from this Context."""
        return self._buffer_stack.pop()
    def get(self, key, default=None):
        return self._data.get(key, default)
    def write(self, string):
        """write a string to this Context's underlying output buffer."""
        self._buffer_stack[-1].write(string)
    def _copy(self):
        c = Context.__new__(Context)
        c._buffer_stack = self._buffer_stack
        c._data = self._data.copy()
        c._with_template = self._with_template
        c.namespaces = self.namespaces
        c.caller_stack = self.caller_stack
        return c
    def locals_(self, d):
        """create a new Context with a copy of this Context's current state, updated with the given dictionary."""
        c = self._copy()
        c._data.update(d)
        return c
    def clean_inheritance_tokens(self):
        """create a new copy of this Context with tokens related to inheritance state removed."""
        c = self._copy()
        x = c._data
        x.pop('self', None)
        x.pop('parent', None)
        x.pop('next', None)
        return c

class _StackFacade(object):
    def __init__(self, stack):
        self.target = stack
    def __getattr__(self, key):
        return getattr(self.target[-1], key)
        
class Undefined(object):
    """represents an undefined value in a template."""
    def __str__(self):
        raise NameError("Undefined")
UNDEFINED = Undefined()

   
class Namespace(object):
    """provides access to collections of rendering methods, which can be local, from other templates, or from imported modules"""
    def __init__(self, name, context, module=None, template=None, templateuri=None, callables=None, inherits=None, populate_self=True):
        self.name = name
        self._module = module
        if templateuri is not None:
            self.template = _lookup_template(context, templateuri)
        else:
            self.template = template
        self.context = context
        self.inherits = inherits
        if callables is not None:
            self.callables = dict([(c.func_name, c) for c in callables])
        else:
            self.callables = None
        if populate_self and self.template is not None:
            (lclcallable, self.context) = _populate_self_namespace(context, self.template, self_ns=self)

    module = property(lambda s:s._module or s.template.module)
    filename = property(lambda s:s._module and s._module.__file__ or s.template.filename)
    
    def __getattr__(self, key):
        if self.callables is not None:
            try:
                return self.callables[key]
            except KeyError:
                pass
        if self.template is not None:
            if key == 'body':
                callable_ = self.template.module.render
            else:
                try:
                    callable_ = self.template.get_def(key).callable_
                except AttributeError:
                    callable_ = None
            if callable_ is not None:
                return lambda *args, **kwargs:callable_(self.context, *args, **kwargs)
        if self._module is not None:
            try:
                callable_ = getattr(self._module, key)
                return lambda *args, **kwargs:callable_(self.context, *args, **kwargs)
            except AttributeError:
                pass
        if self.inherits is not None:
            return getattr(self.inherits, key)
        raise exceptions.RuntimeException("Namespace '%s' has no member '%s'" % (self.name, key))

def capture(context, callable_, *args, **kwargs):
    """execute the given template def, capturing the output into a buffer."""
    context.push_buffer()
    try:
        callable_(*args, **kwargs)
    finally:
        buf = context.pop_buffer()
        return buf.getvalue()
        
def include_file(context, uri, import_symbols):
    """locate the template from the given uri and include it in the current output."""
    template = _lookup_template(context, uri)
    (callable_, ctx) = _populate_self_namespace(context.clean_inheritance_tokens(), template)
    callable_(ctx)
        
def inherit_from(context, uri):
    """called by the _inherit method in template modules to set up the inheritance chain at the start
    of a template's execution."""
    template = _lookup_template(context, uri)
    self_ns = context['self']
    ih = self_ns
    while ih.inherits is not None:
        ih = ih.inherits
    lclcontext = context.locals_({'next':ih})
    ih.inherits = Namespace("self:%s" % template.description, lclcontext, template = template, populate_self=False)
    context._data['parent'] = lclcontext._data['local'] = ih.inherits
    callable_ = getattr(template.module, '_mako_inherit', None)
    if callable_  is not None:
        return callable_(lclcontext)
    else:
        gen_ns = getattr(template.module, '_mako_generate_namespaces', None)
        if gen_ns is not None:
            gen_ns(context)
        return (template.callable_, lclcontext)

def _lookup_template(context, uri):
    lookup = context._with_template.lookup
    return lookup.get_template(uri)

def _populate_self_namespace(context, template, self_ns=None):
    if self_ns is None:
        self_ns = Namespace('self:%s' % template.description, context, template=template, populate_self=False)
    context._data['self'] = context._data['local'] = self_ns
    if hasattr(template.module, '_mako_inherit'):
        return template.module._mako_inherit(context)
    else:
        return (template.callable_, context)

def _render(template, callable_, args, data, as_unicode=False):
    """create a Context and return the string output of the given template and template callable."""
    if as_unicode:
        buf = util.FastEncodingBuffer()
    elif template.output_encoding:
        buf = util.FastEncodingBuffer(template.output_encoding)
    else:
        buf = util.StringIO()
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
    context._with_template = template
    # create polymorphic 'self' namespace for this template with possibly updated context
    (inherit, lclcontext) = _populate_self_namespace(context, template)
    if callable_.__name__ == 'render':
        # if main render method, call from the base of the inheritance stack
        _exec_template(inherit, lclcontext, args=args, kwargs=kwargs)
    else:
        # otherwise, call the actual rendering method specified
        _exec_template(callable_, context, args=args, kwargs=kwargs)
        
def _exec_template(callable_, context, args=None, kwargs=None):
    """execute a rendering callable given the callable, a Context, and optional explicit arguments

    the contextual Template will be located if it exists, and the error handling options specified
    on that Template will be interpreted here.
    """
    template = context._with_template
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
                # TODO - friendly error formatting
                source = _get_template_source(callable_)
                raise error
    else:
        callable_(context, *args, **kwargs)
