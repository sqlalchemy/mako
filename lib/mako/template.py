# template.py
# Copyright (C) 2006 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

"""provides the Template class, a facade for parsing, generating and executing template strings,
as well as template runtime operations."""

from mako.lexer import Lexer
from mako import codegen
from mako import runtime, util, exceptions
import imp, time, weakref, tempfile, shutil,  os, stat, posixpath, sys, re


    
class Template(object):
    """a compiled template"""
    def __init__(self, text=None, filename=None, uri=None, format_exceptions=False, error_handler=None, lookup=None, output_encoding=None, module_directory=None, cache_type=None, cache_dir=None):
        """construct a new Template instance using either literal template text, or a previously loaded template module
        
        text - textual template source, or None if a module is to be provided
        
        uri - the uri of this template, or some identifying string. defaults to the 
        full filename given, or "memory:(hex id of this Template)" if no filename
        
        filename - filename of the source template, if any
        
        format_exceptions - catch exceptions and format them into an error display template
        """
        if uri:
            self.module_id = re.sub(r'\W', "_", uri)
            self.uri = uri
        elif filename:
            self.module_id = re.sub(r'\W', "_", filename)
            self.uri = filename
        else:
            self.module_id = "memory:" + hex(id(self))
            self.uri = self.module_id
        
        # if plain text, compile code in memory only
        if text is not None:
            (code, module) = _compile_text(text, self.module_id, filename, self.uri)
            self._code = code
            self._source = text
            ModuleInfo(module, None, self, filename, code, text)
        elif filename is not None:
            # if template filename and a module directory, load
            # a filesystem-based module file, generating if needed
            if module_directory is not None:
                u = self.uri
                if u[0] == '/':
                    u = u[1:]
                path = posixpath.join(module_directory, u + ".py")
                util.verify_directory(posixpath.dirname(path))
                filemtime = os.stat(filename)[stat.ST_MTIME]
                if not os.access(path, os.F_OK) or os.stat(path)[stat.ST_MTIME] < filemtime:
                    util.verify_directory(module_directory)
                    _compile_module_file(file(filename).read(), self.module_id, filename, path, self.uri)
                module = imp.load_source(self.module_id, path, file(path))
                del sys.modules[self.module_id]
                if module._magic_number != codegen.MAGIC_NUMBER:
                    _compile_module_file(file(filename).read(), self.module_id, filename, path, self.uri)
                    module = imp.load_source(self.module_id, path, file(path))
                    del sys.modules[self.module_id]
                ModuleInfo(module, path, self, filename, None, None)
            else:
                # template filename and no module directory, compile code
                # in memory
                (code, module) = _compile_text(file(filename).read(), self.module_id, filename, self.uri)
                self._source = None
                self._code = code
                ModuleInfo(module, None, self, filename, code, None)
        else:
            raise exceptions.RuntimeException("Template requires text or filename")

        self.module = module
        self.filename = filename
        self.callable_ = self.module.render_body
        self.format_exceptions = format_exceptions
        self.error_handler = error_handler
        self.lookup = lookup
        self.output_encoding = output_encoding
        self.cache_type = cache_type
        self.cache_dir = cache_dir

    source = property(lambda self:_get_module_info_from_callable(self.callable_).source, doc="""return the template source code for this Template.""")
    code = property(lambda self:_get_module_info_from_callable(self.callable_).code, doc="""return the module source code for this Template""")
        
    def render(self, *args, **data):
        """render the output of this template as a string.
        
        if the template specifies an output encoding, the string will be encoded accordingly, else the output
        is raw (raw output uses cStringIO and can't handle multibyte characters).
        a Context object is created corresponding to the given data.  Arguments that are explictly
        declared by this template's internal rendering method are also pulled from the given *args, **data 
        members."""
        return runtime._render(self, self.callable_, args, data)
    
    def render_unicode(self, *args, **data):
        """render the output of this template as a unicode object."""
        return runtime._render(self, self.callable_, args, data, as_unicode=True)
        
    def render_context(self, context, *args, **kwargs):
        """render this Template with the given context.  
        
        the data is written to the context's buffer."""
        if getattr(context, '_with_template', None) is None:
            context._with_template = self
        runtime._render_context(self, self.callable_, context, *args, **kwargs)
        
    def get_def(self, name):
        """return a def of this template as an individual Template of its own."""
        return DefTemplate(self, getattr(self.module, "render_%s" % name))
        
class DefTemplate(Template):
    """a Template which represents a callable def in a parent template."""
    def __init__(self, parent, callable_):
        self.parent = parent
        self.callable_ = callable_
    def get_def(self, name):
        return self.parent.get_def(name)

class ModuleInfo(object):
    """stores information about a module currently loaded into memory,
    provides reverse lookups of template source, module source code based on
    a module's identifier."""
    _modules = weakref.WeakValueDictionary()

    def __init__(self, module, module_filename, template, template_filename, module_source, template_source):
        self.module = module
        self.module_filename = module_filename
        self.template_filename = template_filename
        self.module_source = module_source
        self.template_source = template_source
        self._modules[module.__name__] = template._mmarker = self
        if module_filename:
            self._modules[module_filename] = self
    def _get_code(self):
        if self.module_source is not None:
            return self.module_source
        else:
            return file(self.module_filename).read()
    code = property(_get_code)
    def _get_source(self):
        if self.template_source is not None:
            return self.template_source
        else:
            return file(self.template_filename).read()
    source = property(_get_source)
        
def _compile_text(text, identifier, filename, uri):
    node = Lexer(text, filename).parse()
    source = codegen.compile(node, uri, filename)
    cid = identifier
    module = imp.new_module(cid)
    code = compile(source, cid, 'exec')
    exec code in module.__dict__, module.__dict__
    return (source, module)

def _compile_module_file(text, identifier, filename, outputpath, uri):
    (dest, name) = tempfile.mkstemp()
    node = Lexer(text, filename).parse()
    source = codegen.compile(node, uri, filename)
    os.write(dest, source)
    os.close(dest)
    shutil.move(name, outputpath)

def _get_module_info_from_callable(callable_):
    return _get_module_info(callable_.func_globals['__name__'])
    
def _get_module_info(filename):
    return ModuleInfo._modules[filename]
        
