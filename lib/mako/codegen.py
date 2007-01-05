# codegen.py
# Copyright (C) 2006 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

"""provides functionality for rendering a parsetree constructing into module source code."""

import time
import re
from mako.pygen import PythonPrinter
from mako import util, ast, parsetree, filters

MAGIC_NUMBER = 1


def compile(node, uri, filename=None):
    """generate module source code given a parsetree node, uri, and optional source filename"""
    buf = util.FastEncodingBuffer()
    printer = PythonPrinter(buf)
    _GenerateRenderMethod(printer, _CompileContext(uri, filename), node)
    return buf.getvalue()

class _CompileContext(object):
    def __init__(self, uri, filename):
        self.uri = uri
        self.filename = filename
        
class _GenerateRenderMethod(object):
    """a template visitor object which generates the full module source for a template."""
    def __init__(self, printer, compiler, node):
        self.printer = printer
        self.last_source_line = -1
        self.compiler = compiler
        self.node = node
        self.identifier_stack = [None]
        
        self.in_def = isinstance(node, parsetree.DefTag)

        if self.in_def:
            name = "render_" + node.name
            args = node.function_decl.get_argument_expressions()
            filtered = len(node.filter_args.args) > 0 
            buffered = eval(node.attributes.get('buffered', 'False'))
            cached = eval(node.attributes.get('cached', 'False'))
            defs = None
            pagetag = None
        else:
            defs = self.write_toplevel()
            pagetag = self.compiler.pagetag
            name = "render_body"
            if pagetag is not None:
                args = pagetag.body_decl.get_argument_expressions()
                if not pagetag.body_decl.kwargs:
                    args += ['**pageargs']
                cached = eval(pagetag.attributes.get('cached', 'False'))
            else:
                args = ['**pageargs']
                cached = False
            buffered = filtered = False
        if args is None:
            args = ['context']
        else:
            args = [a for a in ['context'] + args]
            
        self.write_render_callable(pagetag or node, name, args, buffered, filtered, cached)
        
        if defs is not None:
            for node in defs:
                _GenerateRenderMethod(printer, compiler, node)
    
    identifiers = property(lambda self:self.identifier_stack[-1])
    
    def write_toplevel(self):
        """traverse a template structure for module-level directives and generate the
        start of module-level code."""
        inherit = []
        namespaces = {}
        module_code = []
        encoding =[None]

        self.compiler.pagetag = None
        
        class FindTopLevel(object):
            def visitInheritTag(s, node):
                inherit.append(node)
            def visitNamespaceTag(s, node):
                namespaces[node.name] = node
            def visitPageTag(s, node):
                self.compiler.pagetag = node
            def visitCode(s, node):
                if node.ismodule:
                    module_code.append(node)
            
        f = FindTopLevel()
        for n in self.node.nodes:
            n.accept_visitor(f)

        self.compiler.namespaces = namespaces

        module_ident = util.Set()
        for n in module_code:
            module_ident = module_ident.union(n.declared_identifiers())

        module_identifiers = _Identifiers()
        module_identifiers.declared = module_ident
        
        # module-level names, python code
        self.printer.writeline("from mako import runtime, filters, cache")
        self.printer.writeline("UNDEFINED = runtime.UNDEFINED")
        self.printer.writeline("_magic_number = %s" % repr(MAGIC_NUMBER))
        self.printer.writeline("_modified_time = %s" % repr(time.time()))
        self.printer.writeline("_template_filename=%s" % repr(self.compiler.filename))
        self.printer.writeline("_template_uri=%s" % repr(self.compiler.uri))
        self.printer.writeline("_template_cache=cache.Cache(__name__, _modified_time)")
        
        main_identifiers = module_identifiers.branch(self.node)
        module_identifiers.topleveldefs = module_identifiers.topleveldefs.union(main_identifiers.topleveldefs)
        [module_identifiers.declared.add(x) for x in ["UNDEFINED"]]
        self.compiler.identifiers = module_identifiers
        self.printer.writeline("_exports = %s" % repr([n.name for n in main_identifiers.topleveldefs.values()]))
        self.printer.write("\n\n")

        if len(module_code):
            self.write_module_code(module_code)

        if len(inherit):
            self.write_namespaces(namespaces)
            self.write_inherit(inherit[-1])
        elif len(namespaces):
            self.write_namespaces(namespaces)

        return main_identifiers.topleveldefs.values()

    def write_render_callable(self, node, name, args, buffered, filtered, cached):
        """write a top-level render callable.
        
        this could be the main render() method or that of a top-level def."""
        self.printer.writeline("def %s(%s):" % (name, ','.join(args)))
        if buffered or filtered or cached:
            self.printer.writeline("context.push_buffer()")
            self.printer.writeline("try:")

        self.identifier_stack.append(self.compiler.identifiers.branch(self.node))
        if not self.in_def and '**pageargs' in args:
            self.identifier_stack[-1].argument_declared.add('pageargs')

        if not self.in_def and (len(self.identifiers.locally_assigned) > 0 or len(self.identifiers.argument_declared)>0):
            self.printer.writeline("__locals = dict(%s)" % ','.join(["%s=%s" % (x, x) for x in self.identifiers.argument_declared]))

        self.write_variable_declares(self.identifiers, toplevel=True)

        for n in self.node.nodes:
            n.accept_visitor(self)

        self.write_def_finish(self.node, buffered, filtered, cached)
        self.printer.writeline(None)
        self.printer.write("\n\n")
        if cached:
            self.write_cache_decorator(node, name, buffered, self.identifiers)
        
    def write_module_code(self, module_code):
        """write module-level template code, i.e. that which is enclosed in <%! %> tags
        in the template."""
        for n in module_code:
            self.write_source_comment(n)
            self.printer.write_indented_block(n.text)

    def write_inherit(self, node):
        """write the module-level inheritance-determination callable."""
        self.printer.writeline("def _mako_inherit(template, context):")
        self.printer.writeline("_mako_generate_namespaces(context)")
        self.printer.writeline("return runtime._inherit_from(context, %s, _template_uri)" % (node.parsed_attributes['file']))
        self.printer.writeline(None)

    def write_namespaces(self, namespaces):
        """write the module-level namespace-generating callable."""
        self.printer.writelines(
            "def _mako_get_namespace(context, name):",
            "try:",
            "return context.namespaces[(__name__, name)]",
            "except KeyError:",
            "_mako_generate_namespaces(context)",
            "return context.namespaces[(__name__, name)]",
            None,None
            )
        self.printer.writeline("def _mako_generate_namespaces(context):")
        for node in namespaces.values():
            if node.attributes.has_key('import'):
                self.compiler.has_ns_imports = True
            self.write_source_comment(node)
            if len(node.nodes):
                self.printer.writeline("def make_namespace():")
                export = []
                identifiers = self.compiler.identifiers.branch(node)
                class NSDefVisitor(object):
                    def visitDefTag(s, node):
                        self.write_inline_def(node, identifiers, nested=False)
                        export.append(node.name)
                vis = NSDefVisitor()
                for n in node.nodes:
                    n.accept_visitor(vis)
                self.printer.writeline("return [%s]" % (','.join(export)))
                self.printer.writeline(None)
                callable_name = "make_namespace()"
            else:
                callable_name = "None"
            self.printer.writeline("ns = runtime.Namespace(%s, context._clean_inheritance_tokens(), templateuri=%s, callables=%s, calling_uri=_template_uri, module=%s)" % (repr(node.name), node.parsed_attributes.get('file', 'None'), callable_name, node.parsed_attributes.get('module', 'None')))
            if eval(node.attributes.get('inheritable', "False")):
                self.printer.writeline("context['self'].%s = ns" % (node.name))
            self.printer.writeline("context.namespaces[(__name__, %s)] = ns" % repr(node.name))
            self.printer.write("\n")
        if not len(namespaces):
            self.printer.writeline("pass")
        self.printer.writeline(None)
            
    def write_variable_declares(self, identifiers, toplevel=False, limit=None):
        """write variable declarations at the top of a function.
        
        the variable declarations are in the form of callable definitions for defs and/or
        name lookup within the function's context argument.  the names declared are based on the
        names that are referenced in the function body, which don't otherwise have any explicit
        assignment operation.  names that are assigned within the body are assumed to be 
        locally-scoped variables and are not separately declared.
        
        for def callable definitions, if the def is a top-level callable then a 
        'stub' callable is generated which wraps the current Context into a closure.  if the def
        is not top-level, it is fully rendered as a local closure."""
        
        # collection of all defs available to us in this scope
        comp_idents = dict([(c.name, c) for c in identifiers.defs])
        to_write = util.Set()
        
        # write "context.get()" for all variables we are going to need that arent in the namespace yet
        to_write = to_write.union(identifiers.undeclared)
        
        # write closure functions for closures that we define right here
        to_write = to_write.union(util.Set([c.name for c in identifiers.closuredefs.values()]))

        # remove identifiers that are declared in the argument signature of the callable
        to_write = to_write.difference(identifiers.argument_declared)

        # remove identifiers that we are going to assign to.  in this way we mimic Python's behavior,
        # i.e. assignment to a variable within a block means that variable is now a "locally declared" var,
        # which cannot be referenced beforehand.  
        to_write = to_write.difference(identifiers.locally_declared)
        
        # if a limiting set was sent, constraint to those items in that list
        # (this is used for the caching decorator)
        if limit is not None:
            to_write = to_write.intersection(limit)
        
        if toplevel and getattr(self.compiler, 'has_ns_imports', False):
            self.printer.writeline("_import_ns = {}")
            self.compiler.has_imports = True
            for ident, ns in self.compiler.namespaces.iteritems():
                if ns.attributes.has_key('import'):
                    self.printer.writeline("_mako_get_namespace(context, %s)._populate(_import_ns, %s)" % (repr(ident),  repr(re.split(r'\s*,\s*', ns.attributes['import']))))
                        
        for ident in to_write:
            if ident in comp_idents:
                comp = comp_idents[ident]
                if comp.is_root():
                    self.write_def_decl(comp, identifiers)
                else:
                    self.write_inline_def(comp, identifiers, nested=True)
            elif ident in self.compiler.namespaces:
                self.printer.writeline("%s = _mako_get_namespace(context, %s)" % (ident, repr(ident)))
            else:
                if getattr(self.compiler, 'has_ns_imports', False):
                    self.printer.writeline("%s = _import_ns.get(%s, context.get(%s, UNDEFINED))" % (ident, repr(ident), repr(ident)))
                else:
                    self.printer.writeline("%s = context.get(%s, UNDEFINED)" % (ident, repr(ident)))
        
    def write_source_comment(self, node):
        """write a source comment containing the line number of the corresponding template line."""
        if self.last_source_line != node.lineno:
            self.printer.writeline("# SOURCE LINE %d" % node.lineno)
            self.last_source_line = node.lineno

    def write_def_decl(self, node, identifiers):
        """write a locally-available callable referencing a top-level def"""
        funcname = node.function_decl.funcname
        namedecls = node.function_decl.get_argument_expressions()
        nameargs = node.function_decl.get_argument_expressions(include_defaults=False)
        if not self.in_def and (len(self.identifiers.locally_assigned) > 0 or len(self.identifiers.argument_declared) > 0):
            nameargs.insert(0, 'context.locals_(__locals)')
        else:
            nameargs.insert(0, 'context')
        self.printer.writeline("def %s(%s):" % (funcname, ",".join(namedecls)))
        self.printer.writeline("return render_%s(%s)" % (funcname, ",".join(nameargs)))
        self.printer.writeline(None)
        
    def write_inline_def(self, node, identifiers, nested):
        """write a locally-available def callable inside an enclosing def."""
        namedecls = node.function_decl.get_argument_expressions()
        self.printer.writeline("def %s(%s):" % (node.name, ",".join(namedecls)))
        filtered = len(node.filter_args.args) > 0 
        buffered = eval(node.attributes.get('buffered', 'False'))
        cached = eval(node.attributes.get('cached', 'False'))
        if buffered or filtered or cached:
            printer.writelines(
                "context.push_buffer()",
                "try:"
                )

        identifiers = identifiers.branch(node, nested=nested)

        self.write_variable_declares(identifiers)
        
        self.identifier_stack.append(identifiers)
        for n in node.nodes:
            n.accept_visitor(self)
        self.identifier_stack.pop()
        
        self.write_def_finish(node, buffered, filtered, cached)
        self.printer.writeline(None)
        if cached:
            self.write_cache_decorator(node, node.name, False, identifiers)
        
    def write_def_finish(self, node, buffered, filtered, cached):
        """write the end section of a rendering function, either outermost or inline.
        
        this takes into account if the rendering function was filtered, buffered, etc.
        and closes the corresponding try: block if any, and writes code to retrieve captured content, 
        apply filters, send proper return value."""
        if not buffered and not cached and not filtered:
            self.printer.writeline("return ''")
        if buffered or filtered or cached:
            self.printer.writeline("finally:")
            self.printer.writeline("_buf = context.pop_buffer()")
            s = "_buf.getvalue()"
            if filtered:
                s = self.create_filter_callable(node.filter_args.args, s)
            self.printer.writeline(None)
            if buffered or cached:
                self.printer.writeline("return %s" % s)
            else:
                self.printer.writeline("context.write(%s)" % s)
                self.printer.writeline("return ''")

    def write_cache_decorator(self, node_or_pagetag, name, buffered, identifiers):
        """write a post-function decorator to replace a rendering callable with a cached version of itself."""
        self.printer.writeline("__%s = %s" % (name, name))
        cachekey = node_or_pagetag.parsed_attributes.get('cache_key', repr(name))
        cacheargs = {}
        print node_or_pagetag
        for arg in (('cache_type', 'type'), ('cache_dir', 'data_dir'), ('cache_timeout', 'expiretime')):
            val = node_or_pagetag.parsed_attributes.get(arg[0], None)
            if val is not None:
                if arg[1] == 'expiretime':
                    cacheargs[arg[1]] = int(eval(val))
                else:
                    cacheargs[arg[1]] = val
            else:
                if self.compiler.pagetag is not None:
                    val = self.compiler.pagetag.parsed_attributes.get(arg[0], None)
                    if val is not None:
                        if arg[1] == 'expiretime':
                            cacheargs[arg[1]] == int(eval(val))
                        else:
                            cacheargs[arg[1]] = val
            
        self.printer.writeline("def %s(context, *args, **kwargs):" % name)

        self.write_variable_declares(identifiers, limit=node_or_pagetag.undeclared_identifiers())
        if buffered:
            self.printer.writelines(
                    "return context.get('local').get_cached(%s, %screatefunc=lambda:__%s(context, *args, **kwargs))" % (cachekey, ''.join(["%s=%s, " % (k,v) for k, v in cacheargs.iteritems()]), name),
                None
            )
        else:
            self.printer.writelines(
                    "context.write(context.get('local').get_cached(%s, %screatefunc=lambda:__%s(context, *args, **kwargs)))" % (cachekey, ''.join(["%s=%s, " % (k,v) for k, v in cacheargs.iteritems()]), name),
                    "return ''",
                None
            )

    def create_filter_callable(self, args, target):
        """write a filter-applying expression based on the filters present in the given 
        filter names, adjusting for the global 'default' filter aliases as needed."""
        d = dict([(k, "filters." + v.func_name) for k, v in filters.DEFAULT_ESCAPES.iteritems()])
        
        if self.compiler.pagetag:
            args += self.compiler.pagetag.filter_args.args
        for e in args:
            # if filter given as a function, get just the identifier portion
            m = re.match(r'(.+?)(\(.*\))', e)
            if m:
                (ident, fargs) = m.group(1,2)
                f = d.get(ident, ident)
                e = f + fargs
            else:
                e = d.get(e, e)
            target = "%s(%s)" % (e, target)
        return target
        
    def visitExpression(self, node):
        self.write_source_comment(node)
        if len(node.escapes) or (self.compiler.pagetag is not None and len(self.compiler.pagetag.filter_args.args)):
            s = self.create_filter_callable(node.escapes_code.args, "unicode(%s)" % node.text)
            self.printer.writeline("context.write(%s)" % s)
        else:
            self.printer.writeline("context.write(unicode(%s))" % node.text)
            
    def visitControlLine(self, node):
        if node.isend:
            self.printer.writeline(None)
        else:
            self.write_source_comment(node)
            self.printer.writeline(node.text)
    def visitText(self, node):
        self.write_source_comment(node)
        self.printer.writeline("context.write(%s)" % repr(node.content))
    def visitTextTag(self, node):
        filtered = len(node.filter_args.args) > 0
        if filtered:
            self.printer.writelines(
                "context.push_buffer()",
                "try:",
            )
        for n in node.nodes:
            n.accept_visitor(self)
        if filtered:
            self.printer.writelines(
                "finally:",
                "_buf = context.pop_buffer()",
                "context.write(%s)" % self.create_filter_callable(node.filter_args.args, "_buf.getvalue()"),
                None
                )
        
    def visitCode(self, node):
        if not node.ismodule:
            self.write_source_comment(node)
            self.printer.write_indented_block(node.text)

            if not self.in_def and len(self.identifiers.locally_assigned) > 0:
                # if we are the "template" def, fudge locally declared/modified variables into the "__locals" dictionary,
                # which is used for def calls within the same template, to simulate "enclosing scope"
                self.printer.writeline('__locals.update(dict([(k, locals()[k]) for k in [%s]]))' % ','.join([repr(x) for x in node.declared_identifiers()]))
                
    def visitIncludeTag(self, node):
        self.write_source_comment(node)
        self.printer.writeline("runtime._include_file(context, %s, _template_uri)" % (node.parsed_attributes['file']))

    def visitNamespaceTag(self, node):
        pass
            
    def visitDefTag(self, node):
        pass

    def visitCallTag(self, node):
        self.printer.writeline("def ccall(caller):")
        export = ['body']
        callable_identifiers = self.identifiers.branch(node, nested=True)
        body_identifiers = callable_identifiers.branch(node, nested=False)
        body_identifiers.add_declared('caller')
        callable_identifiers.add_declared('caller')
        
        self.identifier_stack.append(body_identifiers)
        class DefVisitor(object):
            def visitDefTag(s, node):
                self.write_inline_def(node, callable_identifiers, nested=False)
                export.append(node.name)
                # remove defs that are within the <%call> from the "closuredefs" defined
                # in the body, so they dont render twice
                del body_identifiers.closuredefs[node.name]
        vis = DefVisitor()
        for n in node.nodes:
            n.accept_visitor(vis)
        self.identifier_stack.pop()
        
        bodyargs = node.body_decl.get_argument_expressions()    
        self.printer.writeline("def body(%s):" % ','.join(bodyargs))
        # TODO: figure out best way to specify buffering/nonbuffering (at call time would be better)
        buffered = False
        if buffered:
            self.printer.writelines(
                "context.push_buffer()",
                "try:"
            )
        self.write_variable_declares(body_identifiers)
        self.identifier_stack.append(body_identifiers)
        for n in node.nodes:
            n.accept_visitor(self)
        self.identifier_stack.pop()
        
        self.write_def_finish(node, buffered, False, False)
        self.printer.writelines(
            None,
            "return [%s]" % (','.join(export)),
            None
        )

        self.printer.writelines(
            # push on global "caller" to be picked up by the next ccall
            "context.caller_stack.append(runtime.Namespace('caller', context, callables=ccall(context.caller_stack[-1])))",
            "try:")
        self.write_source_comment(node)
        self.printer.writelines(
                "context.write(unicode(%s))" % node.attributes['expr'],
            "finally:",
                # pop it off
                "context.caller_stack.pop()",
            None
        )

class _Identifiers(object):
    """tracks the status of identifier names as template code is rendered."""
    def __init__(self, node=None, parent=None, nested=False):
        if parent is not None:
            # things that have already been declared in an enclosing namespace (i.e. names we can just use)
            self.declared = util.Set(parent.declared).union([c.name for c in parent.closuredefs.values()]).union(parent.locally_declared).union(parent.argument_declared)
            
            # if these identifiers correspond to a "nested" scope, it means whatever the 
            # parent identifiers had as undeclared will have been declared by that parent, 
            # and therefore we have them in our scope.
            if nested:
                self.declared = self.declared.union(parent.undeclared)
            
            # top level defs that are available
            self.topleveldefs = util.SetLikeDict(**parent.topleveldefs)
        else:
            self.declared = util.Set()
            self.topleveldefs = util.SetLikeDict()
        
        # things within this level that are referenced before they are declared (e.g. assigned to)
        self.undeclared = util.Set()
        
        # things that are declared locally.  some of these things could be in the "undeclared"
        # list as well if they are referenced before declared
        self.locally_declared = util.Set()
    
        # assignments made in explicit python blocks.  these will be propigated to 
        # the context of local def calls.
        self.locally_assigned = util.Set()
        
        # things that are declared in the argument signature of the def callable
        self.argument_declared = util.Set()
        
        # closure defs that are defined in this level
        self.closuredefs = util.SetLikeDict()
        
        self.node = node
        
        if node is not None:
            node.accept_visitor(self)
        
    def branch(self, node, **kwargs):
        """create a new Identifiers for a new Node, with this Identifiers as the parent."""
        return _Identifiers(node, self, **kwargs)
    
    defs = property(lambda self:util.Set(self.topleveldefs.union(self.closuredefs).values()))
    
    def __repr__(self):
        return "Identifiers(declared=%s, locally_declared=%s, undeclared=%s, topleveldefs=%s, closuredefs=%s, argumenetdeclared=%s)" % (repr(list(self.declared)), repr(list(self.locally_declared)), repr(list(self.undeclared)), repr([c.name for c in self.topleveldefs.values()]), repr([c.name for c in self.closuredefs.values()]), repr(self.argument_declared))
        
    def check_declared(self, node):
        """update the state of this Identifiers with the undeclared and declared identifiers of the given node."""
        for ident in node.undeclared_identifiers():
            if ident != 'context' and ident not in self.declared.union(self.locally_declared):
                self.undeclared.add(ident)
        for ident in node.declared_identifiers():
            self.locally_declared.add(ident)
    
    def add_declared(self, ident):
        self.declared.add(ident)
        if ident in self.undeclared:
            self.undeclared.remove(ident)
                        
    def visitExpression(self, node):
        self.check_declared(node)
    def visitControlLine(self, node):
        self.check_declared(node)
    def visitCode(self, node):
        if not node.ismodule:
            self.check_declared(node)
            self.locally_assigned = self.locally_assigned.union(node.declared_identifiers())
    def visitDefTag(self, node):
        if node.is_root():
            self.topleveldefs[node.name] = node
        elif node is not self.node:
            self.closuredefs[node.name] = node
        for ident in node.undeclared_identifiers():
            if ident != 'context' and ident not in self.declared.union(self.locally_declared):
                self.undeclared.add(ident)
        # visit defs only one level deep
        if node is self.node:
            for ident in node.declared_identifiers():
                self.argument_declared.add(ident)
            for n in node.nodes:
                n.accept_visitor(self)
    def visitIncludeTag(self, node):
        self.check_declared(node)
    def visitPageTag(self, node):
        for ident in node.declared_identifiers():
            self.argument_declared.add(ident)
        self.check_declared(node)
                    
    def visitCallTag(self, node):
        if node is self.node:
            for ident in node.undeclared_identifiers():
                if ident != 'context' and ident not in self.declared.union(self.locally_declared):
                    self.undeclared.add(ident)
            for ident in node.declared_identifiers():
                self.argument_declared.add(ident)
            for n in node.nodes:
                n.accept_visitor(self)
        else:
            for ident in node.undeclared_identifiers():
                if ident != 'context' and ident not in self.declared.union(self.locally_declared):
                    self.undeclared.add(ident)
                
