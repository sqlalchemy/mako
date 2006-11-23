# runtime.py
# Copyright (C) 2006 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

"""provides the Context class, the runtime namespace for templates."""
from mako import exceptions, util
import inspect
        
class Context(object):
    """provides runtime namespace and output buffer for templates."""
    def __init__(self, buffer, **data):
        self.buffer = buffer
        self._argstack = [data]
        self.with_template = None
        data['args'] = _AttrFacade(self)
    def __getitem__(self, key):
        return self._argstack[-1][key]
    def get(self, key, default=None):
        return self._argstack[-1].get(key, default)
    def write(self, string):
        self.buffer.write(string)
    def push(self, args):
        x = self._argstack[-1].copy()
        x.update(args)
        self._argstack.append(x)
    def pop(self):
        self._argstack.pop()
    def locals_(self, d):
        c = Context.__new__(Context)
        c.buffer = self.buffer
        c._argstack = [x for x in self._argstack]
        c.with_template = self.with_template
        if c.with_template is None:
            raise "hi"
        c.push(d)
        return c

class _AttrFacade(object):
    def __init__(self, ctx):
        self.ctx = ctx
    def __getattr__(self, key):
        return self.ctx[key]
            
class Undefined(object):
    """represtents undefined values"""
    def __str__(self):
        raise NameError("Undefined")
UNDEFINED = Undefined()
        
        
class Namespace(object):
    """provides access to collections of rendering methods, which can be local, from other templates, or from imported modules"""
    def __init__(self, name, module=None, template=None, callables=None, inherits=None):
        self.name = name
        self.module = module
        self.template = template
        self.inherits = inherits
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
            if key == 'body':
                callable_ = self.template.module.render
            else:
                try:
                    callable_ = self.template.get_component(key).callable_
                except AttributeError:
                    callable_ = None
            if callable_ is not None:
                return lambda *args, **kwargs:callable_(context, *args, **kwargs)
        if self.module is not None:
            try:
                callable_ = getattr(self.module, key)
                return lambda *args, **kwargs:callable_(context, *args, **kwargs)
            except AttributeError:
                pass
        if self.inherits is not None:
            return self.inherits.contextual_callable(context, key)
        raise exceptions.RuntimeException("Namespace '%s' has no member '%s'" % (self.name, key))

class ContextualNamespace(Namespace):
    def __init__(self, name, context, **kwargs):
        super(ContextualNamespace, self).__init__(name, **kwargs)
        self.context = context
    def __getattr__(self, key):
        return self.contextual_callable(self.context, key)

def _lookup_template(context, uri):
    lookup = context.with_template.lookup
    return lookup.get_template(uri)

def include_file(context, uri, import_symbols):
    lookup = context.with_template.lookup
    template = lookup.get_template(uri)
    template.callable_(context)
        
def inherit_from(context, uri):
    template = _lookup_template(context, uri)
    self_ns = context.get('self', None)
    if self_ns is None:
        fromtempl = context.with_template
        self_ns = ContextualNamespace('self', context, template=fromtempl)
        context._argstack[-1]['self'] = self_ns
    ih = self_ns
    while ih.inherits is not None:
        ih = ih.inherits
    lclcontext = context.locals_({'next':ih})
    ih.inherits = ContextualNamespace('self', lclcontext, template = template)
    context._argstack[-1]['parent'] = ih.inherits
    callable_ = getattr(template.module, '_inherit', getattr(template.module, 'render'))
    callable_(lclcontext)
    
def _render(template, callable_, args, data, as_unicode=False):
    """given a Template and a callable_ from that template, create a Context and return the string output."""
    if as_unicode:
        buf = util.FastEncodingBuffer()
    elif template.output_encoding:
        buf = util.FastEncodingBuffer(template.output_encoding)
    else:
        buf = util.StringIO()
    context = Context(buf, **data)
    kwargs = {}
    if callable_.__name__ == 'render':
        callable_ = getattr(template.module, '_inherit', callable_)
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
